import random
import csv
import time
import sys
import urllib
import argparse
import math
import struct

#from geopy.distance import distance as get_dist
# This is roughly 15x faster although up to 0.5% off
from geopy.distance import great_circle as dist_func

import blacklist
import planes

class Route(object):
	segment_duration_cache = {}
	
	def __init__(self, waypoints=[]):
		self.waypoints = waypoints
		
	def __repr__(self):
		return "<Route %s>" % ",".join([a['ident'] for a in self.waypoints])
		
	def generate_coords(self):
		"""Generate lat,long pairs for seq"""
		return [airport['latitude_deg'] + ',' + airport['longitude_deg'] for airport in self.waypoints]
				
	@staticmethod
	def get_segment_length(waypoint1, waypoint2, data, args):
		length = get_dist_from_cache(data['dist_cache'], waypoint1, waypoint2) * (1.0 + args.routing_overhead_pct / 100.0)
		return length	
		
	@staticmethod
	def get_segment_duration(plane, waypoint1, waypoint2, data, args):
		key = "%s:%s" % (waypoint1['id'], waypoint2['id'])
		if key in Route.segment_duration_cache:
			return Route.segment_duration_cache[key]
		dist = Route.get_segment_length(waypoint1, waypoint2, data, args)
		# Ensure duplicate waypoints are heavily penalized. This is needed due to some other bug...
		if dist == 0.0:
			dist = 9999.9
		speed = plane['avg_speed_mph']
		if not args.disable_jet_stream_correction:
			lat1, long1 = float(waypoint1['latitude_deg']), float(waypoint1['longitude_deg'])
			lat2, long2 = float(waypoint2['latitude_deg']), float(waypoint2['longitude_deg'])
			lat_avg = (lat2 + lat1) / 2.0
			long_delta = long2 - long1
			src = (lat_avg, 0.0)
			dst = (lat_avg, long_delta)
			eastbound_dist = dist_func(src, dst).mi * (1.0 + args.routing_overhead_pct / 100.0)
			# Due to spherical shape of earth, possible for this calculation to go unstable
			if eastbound_dist >= dist:
				eastbound_dist = dist - 1.0
			if long_delta < 0.0:
				eastbound_dist *= -1
			radians = math.acos(eastbound_dist / dist)
			speed += args.jet_stream_correction_mph * math.cos(radians)
		duration = dist / speed
		Route.segment_duration_cache[key] = (speed, duration)
		return (speed, duration)
		
	@staticmethod
	def valid_segment(plane, waypoint1, waypoint2, data, args):
		if Route.get_segment_length(waypoint1, waypoint2, data, args) < plane['max_range_mi']:
			return True
		else:
			return False
		
	def get_length(self, data, args):
		"""Calcuate travel distance between the sequence of waypoints"""
		dist = 0.0
		for i in range(len(self.waypoints) - 1):
			dist += Route.get_segment_length(self.waypoints[i], self.waypoints[i + 1], data, args)
		return dist
		
	def get_duration(self, data, args):
		dur = 0.0
		for i in range(len(self.waypoints) - 1):
			plane = get_plane(i + 1)
			speed, duration = Route.get_segment_duration(plane, self.waypoints[i], self.waypoints[i + 1], data, args)
			dur += duration
		return dur
		
	def set_waypoints(self, waypoints):
		self.waypoints = waypoints
		
def get_plane(seg_num):
	plane_name = planes.plane_to_segment[seg_num]
	return planes.planes[plane_name]
		
def hash_airport(geo_hash_resolution, airport):
	latitude = float(airport['latitude_deg']) 
	longitude = float(airport['longitude_deg'])
	# Using floored division
	lat_bucket = (latitude + 90) // geo_hash_resolution
	long_bucket = (longitude + 180) // geo_hash_resolution
	hash_key = '%s:%s' % (lat_bucket, long_bucket)
	return hash_key
	
def generate_geo_hash_table(geo_hash_resolution, airports):
	if not geo_hash_resolution:
		geo_hash_resolution = 0.00000001
	table = {}
	for airport in airports:
		hash_key = hash_airport(geo_hash_resolution, airport)
		table[hash_key] = table.get(hash_key, []) + [airport]
		airport['hash_key'] = hash_key
	return table

def generate_dist_cache(prefix, airports):
	"""
	This code is kind of ugly. It implements a custom binary protocol which is 
	faster than loading the cache via cPickle or using the json library. It's also
	about 1/6th the size of a json file and 1/10 as large as a cPickle file.
	
	The protocol is:
		2 bytes - num of entries
		for each entry:
			4 bytes (int) - ASCII version of airport ident
			2 bytes (int) - num of distance values
			for each distance value:
				4 bytes (int) - ASCII version of second airport ident
				4 bytes (float) - distance
	"""
	filepath = '%s/dist_cache.dat' % prefix
	dist_cache = {}
	entries = 0
	try:
		with open(filepath, 'rb', 65536) as cachefile:
			entries = struct.unpack('h', cachefile.read(2))[0]
	except:
		pass
	if entries < len(airports):
		rebuild = raw_input("Cache is missing entries (%i vs %i), do you want to rebuild (y/n)? " % (entries, len(airports)))
		if rebuild.lower() != 'y':
			return
		dist_cache = {}
		try:
			dist_cache = load_dist_cache(prefix, airports)
		except:
			pass
		print 'Rebuilding...'
		try:
			last_update = time.time()
			for i, src in enumerate(airports):
				if src['id'] in dist_cache and len(dist_cache[src['id']]) == len(airports):
					continue
				dists = {}
				for dst in airports:
					dist = get_dist(src, dst)
					dists[dst['id']] = dist
				dist_cache[src['id']] = dists
				if time.time() - last_update > 5.0:
					last_update = time.time()
					pct = float(i) / len(airports) * 100.0
					print "\t%.2f%% complete" % pct
		except KeyboardInterrupt:
			pass
		print "Writing cache to file..."
		st = time.time()
		with open(filepath, 'w') as cachefile:
			cachefile.write(struct.pack('h', len(dist_cache.keys())))
			for key, val in dist_cache.items():
				out = struct.pack('ih', int(key), len(val.keys()))
				fmt = 'if' * len(val.keys())
				args = []
				[args.extend((int(k), v)) for k, v in val.items()]
				out += struct.pack(fmt, *args)
				cachefile.write(out)
		print "Done (%.2fs)" % (time.time() - st)
		dist_cache = {}

def load_dist_cache(prefix, airports):
	filepath = '%s/dist_cache.dat' % prefix
	dist_cache = {}
	st = time.time()
	ids = [airport['id'] for airport in airports]
	with open(filepath, 'rb', 65536) as cachefile:
		print "Loading distance cache..."
		entries = struct.unpack('h', cachefile.read(2))[0]
		for i in xrange(entries):
			src, dist_count = struct.unpack('ih', cachefile.read(6))
			results = struct.unpack('if' * dist_count, cachefile.read(8 * dist_count))
			if str(src) in ids:
				dist_cache[str(src)] = dict(zip([str(dst) for dst in results[::2]], results[1::2]))
	cached = len(dist_cache.keys())
	print "Loaded distance cache in %.2fs, found %i entries." % (time.time() - st, cached)
	return dist_cache
	
def get_dist(src, dst):
	src_coords = (src['latitude_deg'], src['longitude_deg'])
	dst_coords = (dst['latitude_deg'], dst['longitude_deg'])
	dist = dist_func(src_coords, dst_coords).mi
	return dist
	
def get_dist_from_cache(dist_cache, src, dst):
	if src['id'] in dist_cache and dst['id'] in dist_cache[src['id']]:
		return dist_cache[src['id']][dst['id']]
	else:
		return get_dist(src, dst)
	
def load_data(args):
	# Read data
	prefix = args.data_path.rstrip('/')
	with open('%s/runways.csv' % prefix, 'rb') as csvfile:
		runways = list(csv.DictReader(csvfile, delimiter=',', quotechar='"'))
	with open('%s/supplemental_runways.csv' % prefix, 'rb') as csvfile:
		runways.extend(list(csv.DictReader(csvfile, delimiter=',', quotechar='"')))
	with open('%s/airports.csv' % prefix, 'rb') as csvfile:
		airports = list(csv.DictReader(csvfile, delimiter=',', quotechar='"'))
	with open('%s/supplemental_airports.csv' % prefix, 'rb') as csvfile:
		airports.extend(list(csv.DictReader(csvfile, delimiter=',', quotechar='"')))
	with open('%s/countries.csv' % prefix, 'rb') as csvfile:
		countries = list(csv.DictReader(csvfile, delimiter=',', quotechar='"'))

	# Filter out runways that are too short or are not properly paved
	plane = get_plane(1)
	valid_runways = [r for r in runways if int(r.get('length_ft', 0) or 0) >= plane['min_runway_length_ft']]
	
	# Filter out badly paved runways
	#   See ICAO surface definitions: https://en.wikipedia.org/wiki/Runway
	valid_runways = [r for r in valid_runways if r.get('surface', '').upper()[:3] in ['ICE', 'ASP', 'CON', 'BIT', 'PEM']]

	# Filter airports based on whether they contain a valid runway
	airport_ids = [runway['airport_ident'] for runway in valid_runways]
	airport_ids = set(airport_ids)
	candidate_airports = [airport for airport in airports if airport['ident'] in airport_ids]
	
	# Filter out closed airports
	candidate_airports = [airport for airport in candidate_airports if airport['type'] != 'closed']
	
	# Country code lookups
	country_code_to_name = {}
	country_name_to_code = {}
	for country in countries:
		country_code_to_name[country['code']] = country['name']
		country_name_to_code[country['name']] = country['code']

	# Country blacklists
	blacklist_country_codes = []
	for country_name in blacklist.COUNTRY_BLACKLIST:
		try:
			iso_country = country_name_to_code[country_name]
			blacklist_country_codes.append(iso_country)
		except:
			print "warning: country code not found for blacklisted country: %s" % country_name

	# Geo-political overrides
	geo_overrides = {}
	for country_name, current_continent, new_continent in blacklist.GEO_OVERRIDES:
		try:
			iso_country = [country['code'] for country in countries if country['name'] == country_name][0]
			geo_overrides[iso_country] = (current_continent, new_continent)
		except:
			print "warning: country code not found for blacklisted country: %s" % country_name
	if args.disable_geo_overrides:
		geo_overrides = {}

	# Apply blacklists
	valid_airports = []
	for airport in candidate_airports:
		if airport['iso_country'] in blacklist_country_codes:
			continue
		airport['country_name'] = country_code_to_name[airport['iso_country']]
		if airport['iso_country'] in geo_overrides.keys():
			# Allows possible re-assocation of continent
			current_continent, new_continent = geo_overrides[airport['iso_country']]
			if airport['continent'] == current_continent:
				airport['continent'] = new_continent
		if airport['ident'] in blacklist.AIRPORT_BLACKLIST:
			continue
		if airport['iso_region'] in blacklist.ISO_REGION_BLACKLIST:
			continue
		valid_airports.append(airport)
		
	# Add back hardcoded airports if needed
	for airport in airports:
		if int(airport['id']) in args.start_from_airport_ids and airport not in valid_airports: 
			valid_airports.append(airport)
		if airport['ident'] in args.start_from_airport_codes and airport not in valid_airports:
			valid_airports.append(airport)
		
	# Generate lookup table
	valid_airports_by_id = {}
	for airport in valid_airports:
		valid_airports_by_id[str(airport['id'])] = airport

	# Hash airports by lat/long
	table = generate_geo_hash_table(args.geo_hash_resolution_deg, valid_airports)
	
	data = {
		'hash_table': table,
		'all_airports': valid_airports,
		'all_airports_by_id': valid_airports_by_id,
	}

	print "Runway stats:"
	print "\t%i total" % len(runways)
	print "\t%i w/ length > %s ft and paved" % (len(valid_runways), plane['min_runway_length_ft'])
	print "\t%i unique airports" % len(airport_ids)
	print "\t%i airports after applying blacklist" % len(valid_airports)
				
	return data
	
def url_for_route(route, api_key):
	"""URL for a static image showing the path"""
	coords = route.generate_coords()
	base = "http://maps.googleapis.com/maps/api/staticmap?"
	# Notes:
	# 	* Max map size for non-premium api is 640x640, which can be doubled to
	# 	  	1280x1280 using the scale=2 parameter.
	params = {
		'size': '640x320',
		'scale': 2,
		'maptype': 'terrain',
		'key': api_key,
		'path': 'color:0x0000ff|weight:2|' + "|".join(coords),
		'sensor': 'false'
	}
	url = base + urllib.urlencode(params)
	return url
	
def generate_ordered_sequences(waypoint_lists):
	"""
	Given an ordered list of lists of possible choices, generate all possible
	ordered sequences.
	"""
	sequences = []
	if len(waypoint_lists) == 0:
		return []
	if len(waypoint_lists) > 1:
		for node in waypoint_lists[0]:
			for child in generate_ordered_sequences(waypoint_lists[1:]):
				if type(child) == list:
					sequences.append([node] + child)
				else:
					sequences.append([node] + [child])
	else:
		sequences = waypoint_lists[0]
	return sequences
	
class Search(object):
	
	def __init__(self, data, args):
		self.data = data
		self.args = args
		self.setup_search()

	def get_airport_by_id(self, id):
		return self.data['all_airports_by_id'][str(id)]
				
	def get_airports_by_continent(self, continent):
		return self.data['airports_by_continent'][continent]

	def pick_airport(self, waypoints, candidates, max_attempts=None):
		airport = None
		attempts = 0
		if max_attempts is None:
			max_attempts = len(candidates)
		while attempts < max_attempts:
			airport = random.choice(candidates)
			if len(waypoints) == 0:
				return airport
			prev_waypoint = waypoints[-1]
			seg_num = len(waypoints)
			plane = get_plane(seg_num)
			if Route.valid_segment(plane, prev_waypoint, airport, self.data, self.args):
				return airport
			else:
				attempts += 1
		return None
		
	def sort_routes(self, routes):
		return sorted(routes, key=lambda x: x.get_duration(self.data, self.args))

	def update_best_routes(self, best_routes, route):
		best_routes.append(route)
		best_routes = self.sort_routes(best_routes)[:args.num_best_routes]
		return best_routes
		
	def optimize_route(self, route, radius, max_searches):
		waypoint_lists = []
		waypoints = route.waypoints
		best_route = route
		for i, waypoint in enumerate(waypoints):
			if i < len(args.start_from_airport_ids):
				waypoint_lists.append([waypoint])
			else:
				candidates = [candidate for candidate in self.data['all_airports'] if get_dist_from_cache(data['dist_cache'], waypoint, candidate) < radius]
				candidates = [candidate for candidate in candidates if candidate['continent'] == waypoint['continent']]
				candidates = random.sample(candidates, min(12, len(candidates)))
				waypoint_lists.append(candidates)
		all_sequences = generate_ordered_sequences(waypoint_lists)
		sequences = random.sample(all_sequences, min(len(all_sequences), max_searches))
		for i, sequence in enumerate(sequences):		
			best_route = self.update_best_routes([best_route], Route(sequence))[0]
		return best_route, len(sequences)
		
	def setup_search(self):
		print "Setting up search..."
		airports = [random.choice(airports) for airports in self.data['hash_table'].values()]
		airports += [self.get_airport_by_id(airport_id) for airport_id in self.args.start_from_airport_ids]
		self.data['airports'] = airports
		self.data['dist_cache'] = load_dist_cache(self.args.data_path.rstrip('/'), self.data['airports'])
		airports_by_continent = {}
		for airport in airports:
			cont = airport['continent']
			if cont not in airports_by_continent:
				airports_by_continent[cont] = [airport]
			else:
				airports_by_continent[cont].append(airport)	
		self.data['airports_by_continent'] = airports_by_continent

	def run(self):
		search_count = 0
		valid_route_count = 0
		last_log_time = time.time()
		last_search_count = 0
		best_routes = []
		start_time = time.time()
		reshuffle_count = int(args.max_searches / args.geo_hash_shuffles)
		
		print "Running search..."
		
		try:
			while search_count < args.max_searches:
			
				# Do search
				waypoints = []
				visited_continents = []
				while len(visited_continents) < 7:
					remaining = set(self.data['airports_by_continent'].keys()) - set(visited_continents)
					airport = None
					if len(self.args.start_from_airport_ids) > len(waypoints):
						airport_id = self.args.start_from_airport_ids[len(waypoints)]
						airport = self.get_airport_by_id(airport_id)
					elif len(self.args.start_from_continent_codes) > len(visited_continents):
						continent = self.args.start_from_continent_codes[len(visited_continents)]
						airport = self.pick_airport(waypoints, self.get_airports_by_continent(continent), max_attempts=10)
					else:
						continent = random.choice(list(remaining))
						airport = self.pick_airport(waypoints, self.get_airports_by_continent(continent), max_attempts=10)
					if airport is None:
						break
					waypoints.append(airport)
					visited_continents.append(airport['continent'])
				search_count += 1
			
				# Periodic logging
				if time.time() - last_log_time > 5.0:
					if len(best_routes) > 0:
						hrs = best_routes[0].get_duration(data, args)
					else:
						hrs = 0.0
					search_rate = (search_count - last_search_count) / 5.0
					print "Searched %i routes (%i/s) and found %s valid routes (best is %.2f hrs)" % (search_count, search_rate, valid_route_count, hrs)
					last_log_time = time.time()
					last_search_count = search_count
				
				# Perodic shuffling
				if search_count % reshuffle_count == 0:
					self.setup_search()
					print "Completed a batch of %s searches, reshuffled airports in each geo hash." % reshuffle_count
			
				# There were no valid segments from last waypoint
				if len(visited_continents) < 7:
					continue
				valid_route_count += 1
				route = Route(waypoints)
				best_routes = self.update_best_routes(best_routes, route)
				
				# Early exit for fully hardcoded route
				if len(self.args.start_from_airport_ids) == 7:
					break
					
		except KeyboardInterrupt:
			pass
		
		elapsed_time = time.time() - start_time
		
		# Remove dups
		routes = []
		keys = []
		for route in best_routes:
			if repr(route) not in keys:
				routes.append(route)
				keys.append(repr(route))
		best_routes = routes
	
		if not self.args.disable_optimization:
			print "Finished initial search in %.2fs, optimizing..." % elapsed_time
			optimized_routes = []
			optimize_count = 0
			for route in best_routes:
				print "Optimizing %s" % route
				best_route, count = self.optimize_route(route, self.args.optimization_radius_mi, self.args.optimization_max_searches)
				optimized_routes.append(best_route)
				optimize_count += count
				old_dur = route.get_duration(data, args)
				new_dur = best_route.get_duration(data, args)
				delta = (old_dur - new_dur) / old_dur * 100.0
				print "\tReduced route from %.2f to %.2f hrs after searching %s additional routes (%.2f%%)" % (old_dur, new_dur, count, delta)
			optimized_routes = self.sort_routes(optimized_routes)
		else:
			optimize_count = 0
			optimized_routes = best_routes

		elapsed_time = time.time() - start_time

		results = {
			'best_routes': optimized_routes,
			'search_count': search_count,
			'optimize_count': optimize_count,
			'valid_route_count': valid_route_count,
			'elapsed_time': elapsed_time
		}
		return results
	
def arg_summary(args):
	out = "Using args:\r\n"
	for k, v in vars(args).items():
		if type(v) == dict:
			out += "\t%s:\r\n" % k
			for k2, v2 in v.items():
				out += "\t\t%s: %s\r\n" % (k2, v2)
		else:
			out += "\t%s: %s\r\n" % (k, v)
	return out
		
def generate_report(data, args, results):
	
	def get_nearest_airport(airport, kind, radius=1000):
		"""
		For cases when the ideal airport is small, look up the closest airport within 
		a certain radius that may larger or have more services. Radius is in miles.
		"""
		best = (999999, None)
		for candidate in data['airports']:
			if airport['ident'] == candidate['ident']:
				continue
			dist = get_dist_from_cache(data['dist_cache'], airport, candidate)
			if dist < radius and dist < best[0] and candidate['type'] == kind:
				best = (dist, candidate)
		return best
		
	def link_for_airport(airport):
		return airport['home_link'] or airport['wikipedia_link'] or 'https://www.google.com/search?q=%s+airport' % airport['ident']
		
	out = "<html><body>"
	out += "<pre>"
	out += "<h3>Summary</h3>"
	out += "Report generated at %s<br>" % time.ctime()
	out += "<br>%s<br>" % arg_summary(args)
	out += "Completed in %.2fs<br>" % results['elapsed_time']
	out += "Searched %i possible routes<br>" % results['search_count']
	out += "Searched %i additional routes for optimizations<br>" % results['optimize_count']
	out += "Found %i valid routes given mission constraints<br>" % results['valid_route_count']
	out += "Showing top %i<br>" % min(args.num_best_routes, len(results['best_routes']))
	for i, route in enumerate(results['best_routes']):
		out += "<h3>Route #%i</h3>" % (i + 1)
		out += "<img src='%s'>" % url_for_route(route, args.google_api_key)
		out += "<br><br>"
		last_airport = None
		for i, airport in enumerate(route.waypoints):
			seg_length = 0.0
			seg_duration = 0.0
			seg_speed = 0.0
			plane = {}
			if last_airport:
				plane = get_plane(i)
				seg_length = route.get_segment_length(last_airport, airport, data, args)
				seg_speed, seg_duration = route.get_segment_duration(plane, last_airport, airport, data, args)
			last_airport = airport
			out += "<a href=\"%s\">%s</a> %s %s " % (link_for_airport(airport), airport['ident'], airport['continent'], airport['iso_country'])
			out += "(%.00f mi / %.1f hrs / %i mph)<br>" % (seg_length, seg_duration, seg_speed)
			out += "\tname: <a href=\"%s\">%s</a>\r\n" % (link_for_airport(airport), airport.get('name') or 'n/a')
			out += "\tcountry: %s\r\n" % (airport.get('country_name') or 'n/a')
			out += "\televation: %sft\r\n" % (airport.get('elevation_ft') or 'n/a')
			out += "\ttype: %s\r\n" % (airport.get('type') or 'n/a')
			out += "\tplane: %s\r\n" % plane.get('short_name', 'n/a')
			if airport['type'] != "large_airport":
				for kind in ["medium_airport", "large_airport"]:
					dist, alternate = get_nearest_airport(airport, kind)
					if alternate:
						out += "\tnearest alternate %s: <a href=\"%s\">%s</a>, %.2f mi\r\n" % (kind, link_for_airport(alternate), alternate['ident'], dist)
						out += "\t\t<a href=\"%s\">%s</a>, %s\r\n" % (link_for_airport(alternate), alternate['name'], alternate['iso_country'])
					else:
						out += "\tnearest alternate %s: None\r\n" % kind
		out += "Total Distance: %.2f miles\r\n" % route.get_length(data, args)
		out += "Duration: %.2f\r\n" % route.get_duration(data, args)
	out += "</pre></body></html>"
	return out
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Seven Continents Marathon Challenge route solver')

	parser.add_argument('--max-searches', action="store", 
						default=10000000, type=int,
						help="Maximum number of routes to search before terminating.")
	parser.add_argument('--routing-overhead-pct', action="store", 
						default=10, type=int,
						help="Overhead percentage (as a decimal) that should be added to route length to account for routing inefficiencies.")
	parser.add_argument('--start-from-airport-ids', action="store", 
						default="",
						help="Force search to start from a comma separated list of airport ids.")
	parser.add_argument('--start-from-airport-codes', action="store",
						default="",
						help="Force search to start from a comma separated list of airport codes.")
	parser.add_argument('--start-from-continent-codes', action="store",
						default="AN",
						help="Force search to start from a comma separated list of continent codes (NA, EU, etc.).")
	parser.add_argument('--disable-geo-overrides', action='store_true', default=False,
						help='Do not use geo-political overrides to determine whether islands and other countries are part of continents.')
	parser.add_argument('--disable-jet-stream-correction', action='store_true', default=False,
						help='Do not apply a corrections to east and western components of travel using jet stream assumptions.')
	parser.add_argument('--disable-optimization', action='store_true', default=False,
						help='Do not run a secondary optimization pass to look for more efficient airports within each hash bucket.')
	parser.add_argument('--num-best-routes', action="store",
						default=20, type=int,
						help="Number of best routes to store.")
	parser.add_argument('--jet-stream-correction-mph', action="store",
						default=50, type=int,
						help="Speed correction to use, in mph, for eastbound component of travel.")
	parser.add_argument('--google-api-key', action="store",
						default="",
						help="Google maps API key, for displaying route maps (optional)")
	parser.add_argument('--geo-hash-resolution_deg', action="store",
						default=5.0, type=float,
						help="Reduce search space by consolidating airports within geo_hash_resolution_deg degrees of lat/long into a single airport.")
	parser.add_argument('--geo-hash-shuffles', action="store",
						default=10, type=int,
						help="Number of times to reshuffle the airport selected within each geo hash bucket during the search.")
	parser.add_argument('--optimization-radius-mi', action="store",
						default=200, type=int,
						help="Radius in miles to search around each waypoint for alternates.")
	parser.add_argument('--optimization-max-searches', action="store",
						default=250000, type=int,
						help="Maximum number of searches to complete during each route optimization.")
	parser.add_argument('--html-file', action="store",
						default="report.html",
						help="Output report file (default is 'report.html').")
	parser.add_argument('--data-path', action="store",
						default="data/",
						help="Path to CSV files (default is 'data/').")

	args = parser.parse_args()
	
	# Pre-processing for certain arguments
	args.start_from_airport_ids = [int(i) for i in args.start_from_airport_ids.split(',') if i]
	args.start_from_airport_codes = [code.strip() for code in args.start_from_airport_codes.split(',') if code]
	args.start_from_continent_codes = args.start_from_continent_codes.split(',')			
	
	print arg_summary(args)
	
	# Load data from config files and process blacklists
	data = load_data(args)
	
	# Convert codes to ids
	if len(args.start_from_airport_codes) > 0:
		args.start_from_airport_ids = []
		for code in args.start_from_airport_codes:
			for airport in data['all_airports']:
				if airport['ident'] == code:
					args.start_from_airport_ids.append(airport['id'])
	print "start_from_airport_ids: %s" % args.start_from_airport_ids
	
	# Generate distance cache, if needed
	generate_dist_cache(args.data_path.rstrip('/'), data['all_airports'])
			
	# Run search until max_searches reached or terminated
	search = Search(data, args)
	results = search.run()
	
	# Attempt to open results webpage
	print "Generating report..."
	data = generate_report(data, args, results)
	try:
		open(args.html_file, 'w').write(data)
		print "Report written to %s" % args.html_file
	except:
		print "Could not generate html file %s" % args.html_file

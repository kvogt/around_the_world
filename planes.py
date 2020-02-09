# Ranges and speeds are approximate, based on anecdotal conversations with 
# pilots and discussing what they'd be comfortable doing. Actual flight plans 
# are much more complicated and vary depending on the specific rules of each 
# airport. Cruising speeds are based on sampling of a few quoted flight times
# for longer flights (> 4 hrs) where the majority of the flight time is spent
# at close to cruising speed vs. climb / descent.
#
# A better way to do this would be to build an actual flight profile and 
# calcuate fuel weight, cargo weight, passenger weight, etc. But I think we're
# talking about a less than 10% improvement in overall accuracy so I'm not 
# going to do this right now. My basic assumptions are good enough (plane 
# carrying a decent amount of passengers and cargo and lots of fuel).

planes = {
	'737': {
		'name': 'Boeing 737',
		'short_name': '737',
		'max_range_mi': 3000,
		'avg_speed_mph': 480,
		'min_runway_length_ft': 5000,
	},
	'737': {
		'name': 'Airbus 737',
		'short_name': '737',
		'max_range_mi': 3000,
		'avg_speed_mph': 450,
		'min_runway_length_ft': 5000,
	},
	'g450': {
		'name': 'Gulfstream g450',
		'short_name': 'g450',
		'max_range_mi': 4100,
		'avg_speed_mph': 525,
		'min_runway_length_ft': 5000,
	},
	'g550': {
		'name': 'Gulfstream g550',
		'short_name': 'g550',		
		'max_range_mi': 5800,
		'avg_speed_mph': 550,
		'min_runway_length_ft': 5000,
	},
	'g550_lowfuel': {
		'name': 'Gulfstream g550',
		'short_name': 'g550',		
		'max_range_mi': 2700,
		'avg_speed_mph': 550,
		'min_runway_length_ft': 5000,
	},
	'g650': {
		'name': 'Gulfstream g650',
		'short_name': 'g650',
		'max_range_mi': 6500,
		'avg_speed_mph': 575,
		'min_runway_length_ft': 5000,
	},
	'global_6000': {
		'name': 'Global 6000',
		'short_name': 'global_6000',
		'max_range_mi': 6500,
		'avg_speed_mph': 550,
		'min_runway_length_ft': 5000,		
	}
}

plane_to_segment = {
	1: 'g550',
	2: 'global_6000',
	3: 'global_6000',
	4: 'global_6000',
	5: 'global_6000',
	6: 'global_6000',		
}

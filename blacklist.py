# Note:
#   - Exclude state department warning level 3 or 4
#   - Fetched on March 15th, 2019
COUNTRY_BLACKLIST = [
	'Venezuela',
	'Yemen',
	'Haiti',
	'Afghanistan',
	'Somalia',
	'North Korea',
	'South Sudan',
	'Iraq',
	'Iran',
	'Central African Republic',
	'Syria',
	'Mali',
	'Libya',
	'Guinea-Bissau',
	'Turkey',
	'Burkina Faso',
	'Pakistan',
	'Nigeria',
	# 'Democratic Republic of the Congo', ==> this is "CD" and "CG"
	'Congo (Kinshasa)',
	'Congo (Brazzaville)',
	# ========
	'Chad',
	'El Salvador',
	'Sudan',
	'Mauritania',
	'Niger',
	'Honduras',
	'Nicaragua',
	'Lebanon',
	'Burundi',
	# Still not ideal:
	'Algeria',
	'Tunisia',
	'Morocco',
]

# Note:
#  These are added to the blacklist because they're not part of the mainland continent
COUNTRY_BLACKLIST.extend([
	'Saint Vincent and the Grenadines',
	'Seychelles',
	'Antigua and Barbuda',
	'Puerto Rico',
	'Saint Lucia',
	'Saint Kitts and Nevis',
	'Christmas Island',
	'Cook Islands',
	'Guam',
	'Micronesia',
	'Dominican Republic',
	'Martinique',
	'Barbados',
	'Anguilla',
	'Faroe Islands',
	'British Virgin Islands',
	'U.S. Virgin Islands',
	'Solomon Islands',
	'Maldives',
	'Northern Mariana Islands',
	'Marshall Islands',
	'Cayman Islands',
	'Gibraltar',
	'Fiji',
	'Falkland Islands',
	'Iceland',
	'Caribbean Netherlands',
	'Taiwan',
	'Sint Maarten',
	'Jamaica',
	'Cape Verde',
	'Sri Lanka',
	'Guadeloupe',
	'Saint Helena',
	'Bermuda', # Todo: ask about this one
	'Mauritius', # Todo: ask about this one
])

# According to https://web.archive.org/web/20170129230330/http://www.worldmarathonchallenge.com/html/clubs/17.html
# the following countries are considered part of the associated continents because they're on the continent's
# tectonic plate or on the continental shelf.
#
# I used the following references to attempt to determine which tectonic plate a country lies on:
#   https://en.wikipedia.org/wiki/File:Plates_tect2_en.svg
#   https://msnucleus.org/membership/html/k-6/pt/plate/k/ptptk_3a.html

GEO_OVERRIDES = [
	# These are not explicitly mentioned but appear to fit the criteria
	('Trinidad and Tobago', 'NA', 'SA'),	# Border of SA and Carribean plate
	('Aruba', 'NA', 'SA'), 					# Border of SA and Carribean plate
	('Russia', 'EU', 'AS'),					# No part of Russia should be considered EU
]

ISO_REGION_BLACKLIST = [
	'US-HI', 	# Hawaii is all islands
]

# Note:
#   - Referenced by ident field of airports.csv
#.  - Airports must be generally part of the mainland of the continent
AIRPORT_BLACKLIST = [
	'NTMD', # Nuku Hiva Airport, (French Polynesian Islands, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Nuku_Hiva_Airport
	'NTGJ', # Totegegie Airport, (French Polynesian Islands, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Totegegie_Airport
	'PMDY', # Henderson Field (US territory but not continentual US)
			#   https://en.wikipedia.org/wiki/Henderson_Field_(Midway_Atoll)
	'NTTO', # Hao Airport (French Polynesian Islands, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Hao_Airport
	'PKMA', # Eniwetok Airport (Marshall Islands, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Enewetak_Auxiliary_Airfield
	'PLCH', # Cassidy International Airport (part of New Zealand, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Cassidy_International_Airport
	'SCIP', # Mataveri Airport (part of Chile, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Mataveri_International_Airport
	'ANG',  # Angaur Airstrip (island, not really part of Oceana)
			#   https://en.wikipedia.org/wiki/Angaur_Airstrip
	'PWAK', # Wake Island Airfield (island, not really part of Oceana)
			#   https://en.wikipedia.org/wiki/Wake_Island_Airfield
	'LPPI', # Pico Airport (island, middle of Pacific, not really part of Europe)
			#   https://en.wikipedia.org/wiki/Pico_Airport
	'PKWA', # Bucholz Army Air Field (Marshall Islands, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Bucholz_Army_Airfield
	'LPPD', # Joao Paulo II Airport (middle of the Pacific, not part of EU)
			#   https://en.wikipedia.org/wiki/Jo%C3%A3o_Paulo_II_Airport
	'PGSN', # Saipan International Airport (not continental Oceana)
			#   https://en.wikipedia.org/wiki/Saipan_International_Airport
	'PGWT', # Tinian International Airport (not continental Oceana)
			#   https://en.wikipedia.org/wiki/Tinian_International_Airport
	'GCLA', # La Palma Airport (Canary Islands, not mainland EU)
			#   https://en.wikipedia.org/wiki/La_Palma_Airport
	'PTKK', # Chuuk International Airport (island, not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Chuuk_International_Airport
	'C23',  # Peleliu Airport (island, not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Peleliu_Airfield
	'LPAZ', # Santa Maria Airport (island, not part of mainland EU)
			#   https://en.wikipedia.org/wiki/Santa_Maria_Airport_(Azores)
	'PGRO', # Rota International Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Rota_International_Airport
	'LPHR', # Horta Airport (not mainland EU)
			#   https://en.wikipedia.org/wiki/Horta_Airport
	'PTRO', # Babelthuap Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Roman_Tmetuchl_International_Airport
	'NGTA', # Bonriki International Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Bonriki_International_Airport
	'PTPN', # Pohnpei International Airport' (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Pohnpei_International_Airport
	'NTAA', # Faa'a International Airport (French Polynesian, middle of Pacific)
			#   https://en.wikipedia.org/wiki/Faa%27a_International_Airport
	'PKMJ', # Marshall Islands International Airport (middle of pacific)
			#   https://en.wikipedia.org/wiki/Marshall_Islands_International_Airport
	'NTTG', # Rangiroa Airport (French Polynesian, not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Rangiroa_Airport
	'PCIS', # Canton Island Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Canton_Island_Airport
	'ANYN', # Nauru International Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Nauru_International_Airport
	'PHNG', # Kaneohe Bay MCAS (Marion E. Carl Field) Airport (not mainland US)
			#   https://www.airnav.com/airport/PHNG
	'AYKT', # Aropa Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Aropa_Airport
	'AYGA', # Goroka Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Goroka_Airport
	'SJDB', # Duplicate)Bonito Airport (technically Brazil but not South America at all!)
			#   https://en.wikipedia.org/wiki/Bonito_Airport
	'NCAI', # Aitutaki Airport (not mainland Oceana)
			#   https://en.wikipedia.org/wiki/Aitutaki_Airport
	'RPLB', # Subic Bay International Airport (not mainland Asia)
			#   https://en.wikipedia.org/wiki/Subic_Bay_International_Airport
	'PADK', # Adak Airport (not mainland US)
			#   https://en.wikipedia.org/wiki/Adak_Airport
	'FMEE', # Roland Garros Airport (not mainland Africa)
			#   https://en.wikipedia.org/wiki/Roland_Garros_Airport
	'FMNM', # Amborovy Airport (not mainland Africa)
			#	https://en.wikipedia.org/wiki/Amborovy_Airport
	'GVSV', # Sao Pedro Airport (not mainland Africa)
			# 	https://en.wikipedia.org/wiki/Ces%C3%A1ria_%C3%89vora_Airport
	'FM43', # Antsiranana Andrakaka Airport (not mainland Africa)
	'TNCC', # Hato International Airport (not mainland NA - Curacao)
	'TGPY', # Point Salines International Airport (not mainland NA - St. George's)
	'FMEP', # Pierrefonds Airport (not mainland Africa)
	'SBFN', # Fernando de Noronha Airport (island off of brazil)
	'GCXO', # Tenerife Norte Airport (island off Africa but part of Spain)
	'PASY', # Eareckson Air Station (middle of pacific, part of Alaska but not on continent)
	'PAAT', # Casco Cove Coast Guard Station (US base, middle of pacific)
	'CYLT', # Alert Airport in Canada. Fuel and service for military only, gravel runway.
	'FJDG', # Diego Garcia Naval Support Facility, middle of Indian ocean
	'GCRR', # Spanish island, not part of mainland Africa
	'GCTS', # Spanish island, not part of mainland Africa
	'GCLP', # Spanish island, not part of mainland Africa
	
	# If Portuguese archipelago allowed, remove the following:
	'LPMA', # Madeira Airport (part of Portuguese archipelago but to far in the ocean)
	'LPLA', # Lajes Airport (part of Portuguese archipelago but to far in the ocean)
	'LPPS', # Porto Santo Airport (part of Portuguese archipelago but to far in the ocean)
	
	# If Iceland allowed, remove the following:
	'ENSB', # Svalbard Airport (on Iceland but part of Norway / EU, and physically on EU plate)
]
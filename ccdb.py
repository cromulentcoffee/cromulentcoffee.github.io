#!/usr/bin/python

import urllib
import json
import argparse
import sys

##
## Cromulent Coffee database and converting that to GeoJSON
## with address lookups
##

# Destination for command-line args
options = None

# Local cache of geo lookup for addresses
CACHE_FILE = "geocache.json"
geo_cache = {}
geo_loaded = False
geo_dirty = False

###
##  geo cache
#

def geocache_lookup(addr):

    global geo_loaded, geo_cache
    
    if (not geo_loaded):
        try:
            fl = open(CACHE_FILE)
        except:
            # ignore errors opening the cache
            pass
        else:
            s = ""
            for line in fl.readlines():
                s += line
            geo_cache = json.loads(s)
            
        geo_loaded = True
        
    # now look up the cache
    if (addr in geo_cache):
        return geo_cache[addr]

def geocache_add(addr, data):

    global geo_dirty
    
    # add it to memory
    geo_cache[addr] = data
    geo_dirty = True


def geocache_save():

    if (not geo_dirty):
        return

    print "Updating geo cache"
    
    # add it to the file
    fl = open(CACHE_FILE, "w")
    fl.write(json.dumps(geo_cache,
                        indent=4, separators=(',', ': ')))


    
###
##  geo lookup
#

# kuma:tmp balial$ curl -o foo.xml https://maps.googleapis.com/maps/api/geocode/json?address=2821+California+St+San+Francisco,+CA+94115

GOOG_URL = "https://maps.googleapis.com/maps/api/geocode/json?"

def geocode_address(name, addr, geo_opt):

    # Don't lookup anything
    if (geo_opt == "no_lookup"):
        return None

    # consult the cache
    geo = geocache_lookup(addr)
    if (geo is not None):
        return geo[0]
        
    # Don't lookup anything
    if (geo_opt == "no_query"):
        return None

    print "Cached address for '%s' not found, looking up" % name

    # make a URL
    urladdr = urllib.urlencode({"address": addr})
    url = GOOG_URL + urladdr

    # pull a file
    nw = urllib.urlopen(url)

    # read it
    s = ""
    for line in nw.readlines():
        s += line

    # parse it
    js = json.loads(s)

    # pull the lat / long
    loc = js['results'][0]['geometry']['location']
    coord = [float(loc["lng"]), float(loc["lat"])]

    # pull the authorative address (FIXME: use this)
    fa = js['results'][0]['formatted_address']

    # add it to the cache
    geocache_add(addr, (coord, fa))
    
    # the list of floats for json to encode
    return coord
        
###
##  Handling a database entry
#

REQUIRED_FIELDS = ["name", "address", "rating"]
WARNING_FIELDS = ["ig", "url"]
VALID_FIELDS = {"name": None,
                "address": None,
                "location": None,
                "yelp": None,
                "ig": None,
                "rating": None,
                "notes": None,
                "food": None,
}

LATLONG = "coordinates"

# Do nothing when we parse this file
def CCS(**args):
    return args

def NameCCS(args):

    if ("location" in args):
        s = "%s - %s" % (args['name'], args['location'])
    else:
        s = args['name']

    return s

def CheckCCS(args):

    reqs = []
    invs = []
    warns = []
    
    # Make sure required args are all there
    for req in REQUIRED_FIELDS:
        if req not in args.keys():
            reqs.append(req)

    # Make sure all args are valid
    for arg in args.keys():
        if (arg not in VALID_FIELDS.keys()):
            invs.appens(arg)

    # Warn about fields that we should have
    for warn in WARNING_FIELDS:
        if warn not in args.keys():
            warns.append(warn)

    return (reqs, invs, warns)

# Actually process the data
def ParseCCS(args, geo_opt=None):

    # check the entry
    (reqs, invs, warns) = CheckCCS(args)

    if (len(reqs)):
        raise RuntimeError("Missing required fields: %s", reqs)
    
    if (len(invs)):
        raise RuntimeError("Invalid fields specified: %s", invs)

    # Make sure all valid fields with default values are specified
    for field in VALID_FIELDS.keys():
        if ((field not in args.keys())
            and (VALID_FIELDS[field] is not None)):
            args[field] = VALID_FIELDS[field]
        
    # Now look up the lat/long
    # FIXME: insta scrape will probably use lat/long already
    args[LATLONG] = geocode_address(NameCCS(args), args["address"], geo_opt)

    # Then just leave it as a dict
    return args

###
##  converting a CCS dict to geojson dict
#

def ccs2geojson(ccs):
    coords = ccs[LATLONG]
    del ccs[LATLONG]

    geom = { "type": "Point", "coordinates": coords }
    
    feature = { "type": "Feature",
                "properties": ccs,
                "geometry": geom }

    return feature

###
##  v.1 database in Python
#

CCDB = [

    CCS(
        name = "b. Patisserie",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/b-patisserie-san-francisco-2",
        address = "2821 California St San Francisco, CA 94115",
        ig = "bpatisserie",
    ),

    CCS(
        name = "Ritual Coffee Roasters",
        rating = "cromulent",
        location = "Mission",
        yelp = "http://www.yelp.com/biz/ritual-coffee-roasters-san-francisco",
        address = "1026 Valencia Street San Francisco, CA 94110",
        ig = "ritualcoffee" 
    ),

    CCS(
        name = "Ritual Coffee Roasters",
        rating = "cromulent",
        location = "Hayes Valley",
        yelp = "http://www.yelp.com/biz/ritual-coffee-roasters-san-francisco-5",
        address = "432b Octavia St San Francisco, CA 94102",
        ig = "ritualcoffee" 
    ),

    CCS(
        name = "Craftsman and Wolves",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/craftsman-and-wolves-san-francisco",
        address = "746 Valencia St San Francisco, CA 94110",
        ig = "craftsmanwolves" 
    ),

    CCS(
        name = "Craftsman and Wolves",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/craftsman-and-wolves-san-francisco",
        address = "746 Valencia St San Francisco, CA 94110",
        ig = "craftsmanwolves"  
    ),

    CCS(
        name = "The Mill",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-mill-san-francisco",
        address = "736 Divisadero St San Francisco, CA 94117" 
    ),

    CCS(
        name = "Pinhole Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/pinhole-coffee-san-francisco-3",
        address = "231 Cortland Ave San Francisco, CA 94110",
        ig = "pinholecoffee"
    ),

    CCS(
        name = "Bright Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/bright-coffee-monterey",
        address = "281 Lighthouse Ave Monterey, CA 93940" 
    ),

    CCS(
        name = "DeLise",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/delise-san-francisco",
        address = "327 Bay St San Francisco, CA 94133" 
    ),

    CCS(
        name = "Le Marais Bakery",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/le-marais-bakery-san-francisco-4",
        address = "2066 Chestnut St San Francisco, CA 94123" 
    ),

    CCS(
        name = "Snowbird Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/snowbird-coffee-san-francisco",
        address = "1352 A 9th Ave San Francisco, CA 94122" 
    ),

    CCS(
        name = "Linea Caffe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/linea-caffe-san-francisco",
        address = "3417 18th St San Francisco, CA 94110" 
    ),

    CCS(
        name = "Jane on Larkin",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/jane-on-larkin-san-francisco-2",
        address = "925 Larkin St San Francisco, CA 94109" 
    ),

    CCS(
        name = "Contraband Coffee Bar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/contraband-coffee-bar-san-francisco",
        address = "1415 Larkin St San Francisco, CA 94109" 
    ),

    CCS(
        name = "The Brew",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-brew-san-francisco",
        address = "2436 Polk St San Francisco, CA 94109" 
    ),

    CCS(
        name = "Bitter+Sweet",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/bitter-sweet-cupertino",
        address = "20560 Town Center Ln Cupertino, CA 95014" 
    ),

    CCS(
        name = "Saint Frank Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/saint-frank-coffee-san-francisco-2",
        address = "2340 Polk St San Francisco, CA 94109" 
    ),

    CCS(
        name = "Coffee Bar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffee-bar-san-francisco",
        address = "1890 Bryant St San Francisco, CA 94110" 
    ),

    CCS(
        name = "Coffee Bar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffeebar-truckee-3",
        address = "10120 Jibboom St Truckee, CA 96161" 
    ),

    CCS(
        name = "I.V. Coffee Lab",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/i-v-coffee-lab-incline-village",
        address = "907 Tahoe Blvd, Ste 20A, Incline Village, NV 89451",
    ),

    CCS(
        name = "Wrecking Ball Coffee Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/wrecking-ball-coffee-roasters-san-francisco-2",
        address = "2271 Union St San Francisco, CA 94123" 
    ),

    CCS(
        name = "Outerlands",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/outerlands-san-francisco",
        address = "4001 Judah St San Francisco, CA 94122",
        food = "meals"
    ),

    CCS(
        name = "Sextant Coffee Roasters",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/sextant-coffee-roasters-san-francisco",
        address = "1415 Folsom St San Francisco, CA 94103" 
    ),

    CCS(
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "SOMA",
        yelp = "http://www.yelp.com/biz/sightglass-coffee-san-francisco",
        address = "270 Seventh Street San Francisco, CA 94103" 
    ),

    CCS(
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Mission",
        address = "3014 20th Street, San Francisco, CA, 94110",
    ),

    CCS(
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Ferry Building",
        address = "San Francisco Ferry Building, San Francisco, CA, 94111" 
    ),

    CCS(
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Divisadero",
        address = "301 Divisadero St. San Francisco, CA 94117" 
    ),

    CCS(
        name = "Sightglass Coffee",
        rating = "not yet open",
        location = "SFMOMA",
        address = "151 Third Street, San Francisco, CA, 94103",
        notes = "Opening Spring 2016" 
    ),

    CCS(
        name = "Jane on Fillmore",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/jane-on-fillmore-san-francisco",
        address = "2123 Fillmore St San Francisco, CA 94115" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Ferry Building",
        address = "1 Ferry Building, #7 San Francisco, CA 94111" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Hayes Valley",
        address = "315 Linden St. San Francisco, CA 94102" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Heath Ceramics",
        address = "2900 18th St. San Francisco, CA 94110" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Market Square",
        address = "1355 Market St. (at 10th and Stevenson, suite 190) San Francisco, CA 94103" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Mint Plaza",
        address = "66 Mint Street San Francisco, CA 94103" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Palo Alto",
        address = "456 University Ave Palo Alto, CA 94301" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Sansome",
        address = "115 Sansome San Francisco, CA 94104" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        location = "W.C. Morse",
        rating = "cromulent",
        address = "4270 Broadway, Oakland, CA 94611" 
    ),

    CCS(
        name = "Blue Bottle Coffee",
        location = "Webster Street",
        rating = "cromulent",
        address = "300 Webster St. Oakland, CA 94607" 
    ),

    CCS(
        name = "Reveille Coffee Co",
        location = "Castro",
        rating = "cromulent",
        address = "4076 18th St. San Francisco, CA 94114" 
    ),

    CCS(
        name = "Reveille Coffee Co",
        location = "North Beach",
        rating = "cromulent",
        address = "200 Columbus Ave San Francisco, CA 94133" 
    ),

    CCS(
        name = "Reveille Coffee Co",
        location = "Jackson Square",
        rating = "cromulent",
        address = "768 Sansome St San Francisco, CA 94111",
        notes = "Espresso Truck"
    ),

    CCS(
        name = "Andytown Coffee Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/andytown-coffee-roasters-san-francisco",
        address = "3655 Lawton St. San Francsico" 
    ),

    CCS(
        name = "Marla Bakery",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/marla-bakery-san-francisco-2",
        address = "3619 Balboa St San Francisco, CA 94121",
    ),

    CCS(
        name = "Hollow",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/hollow-san-francisco",
        address = "1435 Irving St San Francisco, CA 94122",
    ),

    CCS(
        name = "Hooker's Sweet Treats",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/hookers-sweet-treats-san-francisco",
        address = "442 Hyde St San Francisco, CA 94109" 
    ),

    CCS(
        name = "Mercury",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/mercury-cafe-san-francisco",
        address = "201 Octavia Blvd San Francisco, CA 94102",
    
    ),

    CCS(
        name = "Scarlet City Espresso Bar",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/scarlet-city-espresso-bar-emeryville",
        address = "3960 Adeline St Emeryville, CA 94608",
    ),

    CCS(
        name = "Big Sur Bakery & Restaurant",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/big-sur-bakery-and-restaurant-big-sur-2",
        address = "47540 Hwy 1, Big Sur, CA 93920" 
    ),

    CCS(
        name = "Home",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/home-san-francisco-16",
        address = "1222 Noriega St San Francisco, CA 94122",
    ),

    CCS(
        name = "Red Door Coffee",
        rating = "unverified",
        location = "111 Mina",
        address = "111 Minna St, San Francisco, CA 94105",
    ),

    CCS(
        name = "Red Door Coffee",
        rating = "unverified" ,
        location = "505 Howard",
        address = "505 Howard St, San Francisco, CA 94105",
    ),

    CCS(
        name = "Coffee Cultures",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/coffee-cultures-san-francisco",
        address = "225 Bush St San Francisco, CA 94104",
    ),

    CCS(
        name = "Farley's",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/farleys-san-francisco",
        address = "1315 18th St San Francisco, CA 94107" 
    ),

    CCS(
        name = "Four Barrel Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/four-barrel-coffee-san-francisco",
        address = "375 Valencia St San Francisco, CA 94103" 
    ),

    CCS(
        name = "Four Barrel Coffee Cart",
        rating = "cromulent",
        address = "1 Caledonia St, San Francisco, CA",
        notes = "does it still exist?" 
    ),

    CCS(
        name = "Chocolate Fish Coffee Roasters",
        rating = "unverified",
        location = "East Sacramento",
        address = "4749 Folsom Blvd. Sacramento, CA 95819",
    ),

    CCS(
        name = "Chocolate Fish Coffee Roasters",
        rating = "unverified",
        location = "Downtown",
        address = "400 P Street, Ste 1203, Sacramento, CA 95814",
    ),

    CCS(
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Midtown",
        yelp = "http://www.yelp.com/biz/temple-coffee-roasters-sacramento-2",
        address = "2829 S St Sacramento, CA 95816",
    ),

    CCS(
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Downtown",
        address = "1010 9th Street, Sacramento, CA 95814",
    ),

    CCS(
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Arden Arcade",
        address = "2600 Fair Oaks Boulevard, Sacramento, CA 95864",
    ),

    CCS(
        name = "Elite Audio Coffee Bar",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/elite-audio-coffee-bar-san-francisco",
        address = "893A Folsom St San Francisco, CA 94107",
    ),

    CCS(
        name = "Chapel Hill Coffee",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/chapel-hill-coffee-san-francisco",
        address = "670 Commercial St San Francisco, CA 94111" 
    ),

    CCS(
        name = "Workshop Cafe",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/workshop-cafe-san-francisco",
        address = "180 Montgomery St, Ste 100, San Francisco, CA 94104" 
    ),

    CCS(
        name = "Cibo",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/cibo-sausalito",
        address = "1201 Bridgeway, Sausalito, CA 94965",
    ),

    CCS(
        name = "Front Cafe",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/front-cafe-san-francisco-3",
        address = "150 Mississippi St, San Francisco, CA 94107",
        ig = "FrontSF",
    ),

    CCS(
        name = "Paramo Coffee Company",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/paramo-coffee-company-san-francisco-2",
        address = "4 Embarcadero Ctr. San Francisco, CA 94111" 
    ),

    CCS(
        name = "Trouble Coffee and Coconut Club",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/trouble-coffee-company-san-francisco",
        address = "4033 Judah St San Francisco, CA 94122"
    ),
    
    CCS(
        name = "Flour and Co",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/flour-and-co-san-francisco-3",
        address = "1030 Hyde St San Francisco, CA 94109",
        ig = "flourandco"
    ),

    ]

###
##  database generation
#
def geojson_generate():

    fl = open(options['output'], "w")
    
    # build the geojson feature list from the DB
    features = []
    for ccs in CCDB:
        features.append(ccs2geojson(ParseCCS(ccs)))

        
    # build the master geojson data structure
    geojson = {"type": "FeatureCollection",
               "features": features}
    
    # dump the db
    fl.write(json.dumps(geojson,
                        indent=4, separators=(',', ': ')))

    print "Processed %d locations" % len(features)
    
###
##  database health checking
#
db_errors = []
db_warnings = []

def db_stat(ccs, l, t, d):

    # Nothing to say about this stat
    if (len(l) == 0):
        return
    
    n = NameCCS(ccs)
    d.append("%s -- %s: %s" %(n, t, l))


def db_check():
    print "Checking DB health"

    # collect the stats
    for ccs in CCDB:
        # check the entry
        (reqs, invs, warns) = CheckCCS(ccs)
        db_stat(ccs, reqs, "Required fields missing", db_errors)
        db_stat(ccs, invs, "Invalid fields specified", db_errors)
        db_stat(ccs, warns, "Desired fields missing", db_warnings)

    if (len(db_warnings)):
        print "Warnings:"
        for i in db_warnings:
            print i

    if (len(db_errors)):
        print "Errors:"
        for i in db_errors:
            print i

    print "%d errors, %d warnings" % (len(db_errors), len(db_warnings))
        
###
##  command-line parsing
#

def parse_args():

    global options
    
    parser = argparse.ArgumentParser("cromulent coffee database")

    parser.add_argument("--dbcheck", dest="action", action="store_const",
                        const="dbcheck",
                        help="database health report [default]")

    parser.add_argument("--geojson", dest="action", action="store_const",
                        const="geojson", help="generate the geojson file")

    parser.add_argument("--output", dest="output", nargs=1,
                        help="output file for --geojson, default = 'ccgeo.json'",
                        default="ccgeo.json")

    # parse it
    options = vars(parser.parse_args())

    # XXX: hackily fix up the action
    if (("action" not in options.keys())
        or (options['action'] is None)):
        options['action'] = "dbcheck"


###
##  entrypoint
#
if (__name__ == "__main__"):


    parse_args()

    action = options['action']
    if (action == "dbcheck"):
        db_check()
        geocache_save()
    elif(action == "geojson"):
        geojson_generate()
        geocache_save()
    else:
        raise RuntimeError("unknown action '%s'" % action)
        

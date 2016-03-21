#!/usr/bin/python

import argparse
import random
import urllib
import string
import json
import math
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

REQUIRED_FIELDS = ["name", "address", "rating", "ccid"]
WARNING_FIELDS = ["ig", "url"]
VALID_RATINGS = ["cromulent", "insta-find", "unverified"]
VALID_FIELDS = {"ccid": None,
                "name": None,
                "address": None,
                "location": None,
                "yelp": None,
                "ig": None,
                "url": None,
                "twitter": None,
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
    
    # Make sure required args are all there and non-None
    for req in REQUIRED_FIELDS:
        if (args.get(req, None) is None):
            reqs.append(req)

    # Make sure all args are valid
    for arg in args.keys():
        if (arg not in VALID_FIELDS.keys()):
            invs.append(arg)

    # Warn about fields that we should have
    for warn in WARNING_FIELDS:
        if warn not in args.keys():
            warns.append(warn)

    # make sure it's a valid rating
    if args["rating"] not in VALID_RATINGS:
        invs.append("rating")

    return (reqs, invs, warns)

# Actually process the data
def ParseCCS(args, geo_opt=None):

    # check the entry
    (reqs, invs, warns) = CheckCCS(args)

    if (len(reqs)):
        raise RuntimeError("Missing required fields: %s", reqs)
    
    if (len(invs)):
        raise RuntimeError("Invalid fields/values specified: %s", invs)

    # Make sure all valid fields with default values are specified
    for field in VALID_FIELDS.keys():
        if ((field not in args.keys())
            and (VALID_FIELDS[field] is not None)):
            args[field] = VALID_FIELDS[field]
        elif ((field in args.keys())
              and (args[field] is None)):
            # remove any none fields we used to avoid warnings
                del args[field]
                
    # Now look up the lat/long
    # FIXME: insta scrape will probably use lat/long already
    args[LATLONG] = geocode_address(NameCCS(args), args["address"], geo_opt)

    # Then just leave it as a dict
    return args

# Given insta info in 'i', update ccdb entry 'cc'
def InstaUpdate(cc, i):
    cc["igpost"] = i["posts"][0]

    l = i["location"]
    url = "https://instagram.com/explore/locations/%s/" % l["id"]
    cc["igpost"]["url"] = url
    cc["igid"] = CCIG_PREFIX + str(l["id"])
    
# Make a CC arg list from an instagram record
def InstaCC(i):

    l = i["location"]
    url = "https://instagram.com/explore/locations/%s/" % l["id"]
    
    args = {}
    args["name"] = l["name"]
    args["rating"] = i["rating"]
    args[LATLONG] = [l["longitude"], l["latitude"]]

    # pull the post and patch the URL in. Make the main link
    # to the pic and the image link to the location.
    args["igpost"] = i["posts"][0]
    args["igpost"]["url"] = url

    # populate the insta-id
    args["igid"] = CCIG_PREFIX + str(l["id"])
    
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

## main database of location and cromulence
CCDB = [

    CCS(
        ccid = "ccw8sS8natWs",
        name = "b. Patisserie",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/b-patisserie-san-francisco-2",
        url = "bpatisserie.com/",
        address = "2821 California St San Francisco, CA 94115",
        ig = "bpatisserie",
        twitter = "b_patisserie",
    ),

    CCS(
        ccid = "ccXnwIdiObwT",
        name = "Ritual Coffee Roasters",
        rating = "cromulent",
        location = "Mission",
        yelp = "http://www.yelp.com/biz/ritual-coffee-roasters-san-francisco",
        url = "https://www.ritualroasters.com/",
        address = "1026 Valencia Street San Francisco, CA 94110",
        ig = "ritualcoffee",
        twitter = "ritualcoffee"
    ),

    CCS(
        ccid = "ccfsSuNpaYjY",
        name = "Ritual Coffee Roasters",
        rating = "cromulent",
        location = "Hayes Valley",
        yelp = "http://www.yelp.com/biz/ritual-coffee-roasters-san-francisco-5",
        url = "https://www.ritualroasters.com/",
        address = "432b Octavia St San Francisco, CA 94102",
        ig = "ritualcoffee",
        twitter = "ritualcoffee"
    ),

    CCS(
        ccid = "ccdk_2O_p_in",
        name = "Craftsman and Wolves",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/craftsman-and-wolves-san-francisco",
        url = "http://www.craftsman-wolves.com",
        address = "746 Valencia St San Francisco, CA 94110",
        ig = "craftsmanwolves",
        twitter = "craftsmanwolves"
    ),

    CCS(
        ccid = "ccA3zu7i4rVC",
        name = "The Mill",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-mill-san-francisco",
        url = "www.themillsf.com/",
        address = "736 Divisadero St San Francisco, CA 94117",
        twitter = "TheMillSF",
        ig = "themillsf",
    ),

    CCS(
        ccid = "cc5qKFwzgPP0",
        name = "Pinhole Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/pinhole-coffee-san-francisco-3",
        url = "http://www.pinholecoffee.com",
        address = "231 Cortland Ave San Francisco, CA 94110",
        ig = "pinholecoffee",
        twitter = "PinholeCoffee",
    ),

    CCS(
        ccid = "ccS-fxOpNJLo",
        name = "Bright Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/bright-coffee-monterey",
        url = "http://www.brightcoffeeca.com",
        address = "281 Lighthouse Ave Monterey, CA 93940",
        ig = "brightcoffeeca",
    ),

    CCS(
        ccid = "cc11VzXrwhyb",
        name = "DeLise",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/delise-san-francisco",
        url = "http://www.delisesf.com",
        address = "327 Bay St San Francisco, CA 94133",
        twitter = "DeLiseSF",
        ig = None,
    ),

    CCS(
        ccid = "ccVZxkFFirPT",
        name = "Le Marais Bakery",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/le-marais-bakery-san-francisco-4",
        url = "http://www.lemaraisbakery.com/",
        address = "2066 Chestnut St San Francisco, CA 94123",
        twitter = "lemaraisbakery",
        ig = "lemaraisbakery",
    ),

    CCS(
        ccid = "ccMjuUsCQuoq",
        name = "Snowbird Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/snowbird-coffee-san-francisco",
        url = "http://snowbirdcoffee.com",
        address = "1352 A 9th Ave San Francisco, CA 94122",
        ig = "snowbirdcoffee",
        twitter = "snowbirdcoffee",
    ),

    CCS(
        ccid = "ccI9VQhB0_v9",
        name = "Linea Caffe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/linea-caffe-san-francisco",
        url = "http://www.lineacaffe.com",
        address = "3417 18th St San Francisco, CA 94110",
        twitter = "linea_caffe",
        ig = "lineacaffe",
    ),

    CCS(
        ccid = "cc5o0tCuU_TE",
        name = "Jane on Larkin",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/jane-on-larkin-san-francisco-2",
        url = "http://itsjane.com/larkin/",
        address = "925 Larkin St San Francisco, CA 94109",
        twitter = "JaneonLarkin",
        ig = "janeonlarkin",
    ),

    CCS(
        ccid = "cczQvs2rugmj",
        name = "Jane on Fillmore",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/jane-on-fillmore-san-francisco",
        url = "http://itsjane.com/fillmore/",
        address = "2123 Fillmore St San Francisco, CA 94115",
        ig = "janeonfillmore",
        twitter = "Janeonfillmore",
    ),


    CCS(
        ccid = "ccSAhn9E1RvR",
        name = "Contraband Coffee Bar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/contraband-coffee-bar-san-francisco",
        url = "http://www.contrabandcoffeebar.com",
        address = "1415 Larkin St San Francisco, CA 94109",
        ig = "contrabandsf",
        twitter = "contrabandsf",
    ),

    CCS(
        ccid = "ccR_p6YFpw2e",
        name = "The Brew",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-brew-san-francisco",
        address = "2436 Polk St San Francisco, CA 94109",
        # Darn these don't seem to exist
        url = None,
        ig = None,
    ),

    CCS(
        ccid = "ccjvDFzkXUOO",
        name = "Bitter+Sweet",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/bitter-sweet-cupertino",
        url = "http://bitter-sweet.com",
        address = "20560 Town Center Ln Cupertino, CA 95014",
        twitter = "bitterplussweet",
        ig = "bitter_plus_sweet",
    ),

    CCS(
        ccid = "ccXuvkXj4kNK",
        name = "Saint Frank Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/saint-frank-coffee-san-francisco-2",
        url = "http://www.saintfrankcoffee.com",
        address = "2340 Polk St San Francisco, CA 94109",
        twitter = "stfrankcoffee",
        ig = "saintfrankcoffee",
    ),

    CCS(
        ccid = "ccMVdr13QZs",
        name = "Coffee Bar",
        location = "Bryant",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffee-bar-san-francisco",
        address = "1890 Bryant St San Francisco, CA 94110",
        url = "http://www.coffeebarsf.com/bryant-st",
        ig = "CoffeeBarSF",
        twitter = "CoffeeBarSF",
    ),

    CCS(
        ccid = "ccAjko9zIZUZ",
        name = "Coffee Bar",
        location = "Montgomery",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffee-bar-san-francisco-2",
        address = "101 Montgomery Street, San Francisco, CA 94104",
        url = "http://www.coffeebarsf.com/montgomery",
        ig = "CoffeeBarSF",
        twitter = "CoffeeBarSF",
    ),

    CCS(
        ccid = "ccmFIMGwLo50",
        name = "Coffee Bar",
        location = "Kearny",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffee-bar-san-francisco-4",
        address = "433 Kearny Street, San Francisco, CA 94108",
        url = "http://www.coffeebarsf.com/montgomery",
        ig = "CoffeeBarSF",
        twitter = "CoffeeBarSF",
    ),

    CCS(
        ccid = "ccyRNf07GQtx",
        name = "Coffeebar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffeebar-truckee-3",
        address = "10120 Jibboom St Truckee, CA 96161",
        url = "http://www.coffeebartruckee.com",
        ig = "coffeebar96161",
        twitter = "Coffeebar96161",
    ),

    CCS(
        ccid = "cc3Wp4gG5TJX",
        name = "Coffeebar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/coffeebar-reno-reno-2",
        address = "682 Mount Rose St, Reno, NV 89509",
        url = "http://www.coffeebarreno.com",
        ig = "coffeebar96161",
        twitter = "coffeebar96161",
    ),

    CCS(
        ccid = "ccLiCujGNiLO",
        name = "I.V. Coffee Lab",
        rating = "insta-find",
        yelp = "http://www.yelp.com/biz/i-v-coffee-lab-incline-village",
        address = "907 Tahoe Blvd, Ste 20A, Incline Village, NV 89451",
        ig = "ivcoffeelab",
        # Facebook for now
        url = "https://www.facebook.com/I.V.CoffeeLab",
    ),

    CCS(
        ccid = "cchhQ0DfouBo",
        name = "Wrecking Ball Coffee Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/wrecking-ball-coffee-roasters-san-francisco-2",
        address = "2271 Union St San Francisco, CA 94123",
        url = "http://www.wreckingballcoffee.com",
        ig = "wreckingballcoffee",
        twitter = "wrecking_ball",
    ),

    CCS(
        ccid = "ccwF263nHkS8",
        name = "Outerlands",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/outerlands-san-francisco",
        address = "4001 Judah St San Francisco, CA 94122",
        url = "http://outerlandssf.com",
        ig = "outerlands",
        twitter = "outerlandssf",
        food = "meals",
    ),

    CCS(
        ccid = "ccKxsosdgdoN",
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "SOMA",
        yelp = "http://www.yelp.com/biz/sightglass-coffee-san-francisco",
        address = "270 Seventh Street San Francisco, CA 94103",
        url = "https://www.sightglasscoffee.com",
        twitter = "Sightglass",
        ig = "sightglass",
    ),

    CCS(
        ccid = "ccRr9AQkVgoU",
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Mission",
        yelp = "http://www.yelp.com/biz/sightglass-coffee-san-francisco-3",
        address = "3014 20th Street, San Francisco, CA, 94110",
        url = "https://www.sightglasscoffee.com",
        twitter = "Sightglass",
        ig = "sightglass",
    ),

    CCS(
        ccid = "ccfq2r8JaCVl",
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Ferry Building",
        yelp = "http://www.yelp.com/biz/sightglass-coffee-stand-san-francisco",
        address = "San Francisco Ferry Building, San Francisco, CA, 94111",
        url = "https://www.sightglasscoffee.com",
        twitter = "Sightglass",
        ig = "sightglass",
    ),

    CCS(
        ccid = "ccuFsreEEMRB",
        name = "Sightglass Coffee",
        rating = "cromulent",
        location = "Divisadero",
        yelp = None, # WTF?
        address = "301 Divisadero St. San Francisco, CA 94117",
        url = "https://www.sightglasscoffee.com",
        twitter = "Sightglass",
        ig = "sightglass",
    ),

    CCS(
        ccid = "cc8VZZjQBG81",
        name = "Sightglass Coffee",
        rating = "unverified",
        location = "SFMOMA",
        yelp = None, # not yet
        address = "151 Third Street, San Francisco, CA, 94103",
        notes = "Opening Spring 2016",
        url = "https://www.sightglasscoffee.com",
        twitter = "Sightglass",
        ig = "sightglass",
    ),

    CCS(
        ccid = "ccsx6pSDhXxX",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Ferry Building",
        address = "1 Ferry Building, #7 San Francisco, CA 94111",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-san-francisco-10",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccEPYkUfhFpR",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Hayes Valley",
        address = "315 Linden St. San Francisco, CA 94102",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-san-francisco-8",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccmyEdkXFlmP",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Heath Ceramics",
        address = "2900 18th St. San Francisco, CA 94110",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-san-francisco-9",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccFXVTBx0gxF",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Market Square",
        address = "1355 Market St. (at 10th and Stevenson, suite 190) San Francisco, CA 94103",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-san-francisco-12",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "cc5hYc9P1aF8",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Mint Plaza",
        address = "66 Mint Street San Francisco, CA 94103",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-co-san-francisco-7",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccZ2qELiefHs",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Palo Alto",
        address = "456 University Ave Palo Alto, CA 94301",
        yelp = "http://www.yelp.com/biz/blue-bottle-palo-alto-4",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccSm1872E5cQ",
        name = "Blue Bottle Coffee",
        rating = "cromulent",
        location = "Sansome",
        address = "115 Sansome San Francisco, CA 94104",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-san-francisco-14",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccfHeSSCRblx",
        name = "Blue Bottle Coffee",
        location = "W.C. Morse",
        rating = "cromulent",
        address = "4270 Broadway, Oakland, CA 94611",
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-oakland",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "cc1P2LhRN5qG",
        name = "Blue Bottle Coffee",
        location = "Webster Street",
        rating = "cromulent",
        address = "300 Webster St. Oakland, CA 94607", 
        yelp = "http://www.yelp.com/biz/blue-bottle-coffee-oakland-2",
        url = "https://bluebottlecoffee.com",
        ig = "bluebottle",
        twitter = "bluebottleroast",
    ),

    CCS(
        ccid = "ccTyALVKcoM1",
        name = "Reveille Coffee Co",
        location = "Castro",
        rating = "cromulent",
        address = "4076 18th St. San Francisco, CA 94114",
        url = "http://www.reveillecoffee.com",
        ig = "reveillecoffee",
        twitter = "reveillecoffee",
    ),

    CCS(
        ccid = "ccII6QoCWaJ9",
        name = "Reveille Coffee Co",
        location = "North Beach",
        rating = "cromulent",
        address = "200 Columbus Ave San Francisco, CA 94133",
        url = "http://www.reveillecoffee.com",
        ig = "reveillecoffee",
        twitter = "reveillecoffee",
    ),

    CCS(
        ccid = "ccLJbSUyN2cj",
        name = "Reveille Coffee Co",
        location = "Jackson Square",
        rating = "cromulent",
        address = "768 Sansome St San Francisco, CA 94111",
        url = "http://www.reveillecoffee.com",
        ig = "reveillecoffee",
        twitter = "reveillecoffee",
        notes = "Espresso Truck",
    ),

    CCS(
        ccid = "ccBzXQu9dfYg",
        name = "Andytown Coffee Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/andytown-coffee-roasters-san-francisco",
        address = "3655 Lawton St. San Francsico",
        url = "http://www.andytownsf.com",
        ig = "andytownsf",
        twitter = "andytownsf",
    ),

    CCS(
        ccid = "ccgo-E-1Rgbh",
        name = "Marla Bakery",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/marla-bakery-san-francisco-2",
        address = "3619 Balboa St San Francisco, CA 94121",
        url = "http://www.marlabakery.com",
        ig = "marlabakery",
        twitter = "Marlabakery",
    ),

    CCS(
        ccid = "cc1u-2cK8P96",
        name = "Hollow",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/hollow-san-francisco",
        address = "1435 Irving St San Francisco, CA 94122",
        url = "http://www.hollowsf.com",
        ig = "hollow_sf",
        twitter = "hollowsf",
    ),

    CCS(
        ccid = "ccq4Og2lpRio",
        name = "Hooker's Sweet Treats",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/hookers-sweet-treats-san-francisco",
        address = "442 Hyde St San Francisco, CA 94109",
        url = "http://www.hookerssweettreats.com",
        twitter = "hookerstreats",
        ig = None,
    ),

    CCS(
        ccid = "cckWbYDb47Sk",
        name = "Mercury",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/mercury-cafe-san-francisco",
        address = "201 Octavia Blvd San Francisco, CA 94102",
        url = "http://www.mercurycafe.net",
        twitter = "mercurycafesf",
        ig = None,
    ),

    CCS(
        ccid = "ccu7Jo4mF4rR",
        name = "Scarlet City Espresso Bar",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/scarlet-city-espresso-bar-emeryville",
        address = "3960 Adeline St Emeryville, CA 94608",
        url = "http://www.scarletcityroasting.com",
        ig = "scarletcitycoffee",
        twitter = "TheScarletCity",
    ),

    CCS(
        ccid = "ccmkik5BqCuD",
        name = "Big Sur Bakery & Restaurant",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/big-sur-bakery-and-restaurant-big-sur-2",
        address = "47540 Hwy 1, Big Sur, CA 93920",
        url = "https://www.bigsurbakery.com",
        ig = "bigsurbakery",
        twitter = "BigSurBakery",
    ),

    CCS(
        ccid = "ccw1AeC7d-WP",
        name = "Home",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/home-san-francisco-16",
        address = "1222 Noriega St San Francisco, CA 94122",
        url = "http://www.yelp.com/biz/home-san-francisco-16",
        ig = "homesf",
    ),

    CCS(
        ccid = "ccY5KLmtZOui",
        name = "Red Door Coffee",
        rating = "unverified",
        location = "111 Mina",
        address = "111 Minna St, San Francisco, CA 94105",
        url = "http://reddoorcoffeesf.com",
        ig = "reddoorcoffee",
        twitter = "reddoorcoffee",
    ),

    CCS(
        ccid = "cczT96QbN0iX",
        name = "Red Door Coffee",
        rating = "unverified" ,
        location = "505 Howard",
        address = "505 Howard St, San Francisco, CA 94105",
        url = "http://reddoorcoffeesf.com",
        ig = "reddoorcoffee",
        twitter = "reddoorcoffee",
    ),

    CCS(
        ccid = "ccBPktGNmUI2",
        name = "Coffee Cultures",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/coffee-cultures-san-francisco",
        address = "225 Bush St San Francisco, CA 94104",
        url = "http://coffee-cultures.com",
        ig = "coffeeculturesfidi",
        twitter = "CoffeeCultures1",
    ),

    CCS(
        ccid = "cc_aNvJSAWWk",
        name = "Farley's",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/farleys-san-francisco",
        address = "1315 18th St San Francisco, CA 94107",
        url = "http://www.farleyscoffee.com",
        ig = "farleyscoffee",
        twitter = "farleyscoffee",
    ),

    CCS(
        ccid = "cchu16k-OXCl",
        name = "Four Barrel Coffee",
        location = "Mission",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/four-barrel-coffee-san-francisco",
        address = "375 Valencia St San Francisco, CA 94103",
        url = "http://fourbarrelcoffee.com",
        ig = "fourbarrelcoffee",
        twitter = "fourbarrel",
    ),

    CCS(
        ccid = "cclWoeomJ6Rr",
        name = "Four Barrel Coffee Cart",
        location = "Mission",
        rating = "cromulent",
        address = "1 Caledonia St, San Francisco, CA",
        notes = "does it still exist?",
        url = "http://fourbarrelcoffee.com",
        ig = "fourbarrelcoffee",
        twitter = "fourbarrel",
    ),

    CCS(
        ccid = "ccxNLf9wYnDF",
        name = "Four Barrel Coffee",
        location = "Portola",
        rating = "cromulent",
        address = "2 Burrows St, San Francisco, CA 94134",
        url = "http://fourbarrelcoffee.com",
        ig = "fourbarrelcoffee",
        twitter = "fourbarrel",
    ),

    CCS(
        ccid = "ccoBy4kjUkC4",
        name = "Chocolate Fish Coffee Roasters",
        rating = "unverified",
        location = "East Sacramento",
        address = "4749 Folsom Blvd. Sacramento, CA 95819",
        url = "http://www.chocolatefishcoffee.com",
        ig = "chocfishcoffee",
        twitter = "ChocFishCoffee",
    ),

    CCS(
        ccid = "ccv0YtTzRb6C",
        name = "Chocolate Fish Coffee Roasters",
        rating = "unverified",
        location = "Downtown",
        address = "400 P Street, Ste 1203, Sacramento, CA 95814",
        url = "http://www.chocolatefishcoffee.com",
        ig = "chocfishcoffee",
        twitter = "ChocFishCoffee",
    ),

    CCS(
        ccid = "cc5S3ThchGQy",
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Midtown",
        yelp = "http://www.yelp.com/biz/temple-coffee-roasters-sacramento-2",
        address = "2829 S St Sacramento, CA 95816",
        url = "http://templecoffee.com",
        ig = "templecoffeeroasters",
        twitter = "templecoffee",
    ),

    CCS(
        ccid = "ccpEQ6-uitOq",
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Downtown",
        address = "1010 9th Street, Sacramento, CA 95814",
        url = "http://templecoffee.com",
        ig = "templecoffeeroasters",
        twitter = "templecoffee",
    ),

    CCS(
        ccid = "ccUCGexfMDYc",
        name = "Temple Coffee Roasters",
        rating = "unverified",
        location = "Arden Arcade",
        address = "2600 Fair Oaks Boulevard, Sacramento, CA 95864",
        url = "http://templecoffee.com",
        ig = "templecoffeeroasters",
        twitter = "templecoffee",
    ),

    CCS(
        ccid = "ccx5qmLjPJi0",
        name = "Elite Audio Coffee Bar",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/elite-audio-coffee-bar-san-francisco",
        address = "893A Folsom St San Francisco, CA 94107",
        url = "http://www.eliteaudiosf.com/menu/",
        ig = "eliteaudiocoffeebar",
        twitter = "eliteaudiocafe",
    ),

    CCS(
        ccid = "ccGUmEyy-UVH",
        name = "Chapel Hill Coffee",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/chapel-hill-coffee-san-francisco",
        address = "670 Commercial St San Francisco, CA 94111",
        url = "http://www.chapelhillcoffee.com",
        ig = "chapelcoffee",
        twitter = "chapelcoffee",
    ),

    CCS(
        ccid = "ccWnK52TbJ4d",
        name = "Workshop Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/workshop-cafe-san-francisco",
        address = "180 Montgomery St, Ste 100, San Francisco, CA 94104",
        url = "http://www.workshopcafe.com",
        ig = "workshopcafesf",
        twitter = "workshopcafe",
    ),

    CCS(
        ccid = "ccODqU7dbxKx",
        name = "Cibo",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/cibo-sausalito",
        address = "1201 Bridgeway, Sausalito, CA 94965",
        url = "http://cibosausalito.com/",
        ig = "cibosausalito",
        twitter = "teracibo",
    ),

    CCS(
        ccid = "cczByXRWLCOA",
        name = "Front Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/front-cafe-san-francisco-3",
        address = "150 Mississippi St, San Francisco, CA 94107",
        url = "https://www.frontsf.com",
        ig = "FrontSF",
        twitter = "frontsf",
    ),

    CCS(
        ccid = "ccopya9bQOEQ",
        name = "Paramo Coffee Company",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/paramo-coffee-company-san-francisco-2",
        address = "4 Embarcadero Ctr. San Francisco, CA 94111",
        url = "http://www.paramocoffee.com",
        ig = "paramocoffee",
        twitter = "paramocoffee",
    ),

    CCS(
        ccid = "cc5OHKDo9fVg",
        name = "Trouble Coffee and Coconut Club",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/trouble-coffee-company-san-francisco",
        address = "4033 Judah St San Francisco, CA 94122",
        # I guess we can use the FB page?
        url = "https://www.facebook.com/pages/Trouble-Coffee-and-Coconut-Club/56373211579",
        ig = None,
    ),
    
    CCS(
        ccid = "ccsoA3Clhr2k",
        name = "Espresso Cielo",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/espresso-cielo-santa-monica",
        address = "3101 Main Street, Santa Monica, CA",
        url = "http://espressocielo.com",
        ig = "espressocielo",
        twitter = "espressocielo",
    ),

    CCS(
        ccid = "ccZfwVFkqF1O",
        name = "Mountain Grounds",
        rating = "insta-find",
        yelp = "http://www.yelp.com/biz/mountain-grounds-martinez",
        address = "3750 Alhambra Ave, Ste 2, Martinez, CA 94553",
        # Facebark 'll do
        url = "https://www.facebook.com/pages/Mountain-Grounds/374220416039981",
        twitter = "mtngrounds",
        ig = None,
    ),

    CCS(
        ccid = "cchn8UdqbPML",
        name = "Pacific Bay Coffee Co.",
        rating = "insta-find",
        yelp = "http://www.yelp.com/biz/pacific-bay-coffee-co-and-micro-roastery-walnut-creek",
        url = "http://www.pacificbaycoffee.com",
        address = "1495 Newell Ave, Walnut Creek, California 94596",
        ig = None,
        twitter = "pacbaycoffee",
    ),
    
    CCS(
        ccid = "ccNiq36NEAPk",
        name = "Aviano Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/aviano-coffee-denver",
        url = "http://avianocoffee.com",
        address = "244 Detroit St, Denver, CO 80206",
        twitter = "avianocoffee",
        ig = "avianocoffee",
    ),

    CCS(
        ccid = "ccWLcwJ12sD1",
        name = "Novo Coffee",
        location = "Gilpin",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/novo-coffee-denver-5",
        url = "http://novocoffee.com",
        address = "1700 E 6th Ave, Denver, CO 80218",
        twitter = "novocoffee",
        ig = "novocoffee",
    ),
    
    CCS(
        ccid = "ccz0s2Kq9f-e",
        name = "Thump Coffee",
        location = "Denver",
        rating = "insta-find",
        yelp = "http://www.yelp.com/biz/thump-coffee-denver",
        url = "http://www.thumpcoffee.com",
        address = "1201 E 13th Ave, Denver, CO 80218",
        twitter = "thumpcoffee",
        ig = "thumpcoffee",
    ),
    
    CCS(
        ccid = "ccMe1vaiJiNC",
        name = "Modern Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/modern-coffee-oakland",
        url = "http://moderncoffeeoakland.com",
        address = "411 13th St, Oakland, CA 94612",
        twitter = "Moderncoffee",
        ig = "moderncoffee",
    ),
    
    CCS(
        ccid = "ccG50D8X4CV1",
        name = "Awaken Cafe",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/awaken-cafe-oakland-2",
        url = "http://www.awakencafe.com",
        address = "1429 Broadway Oakland, CA 94612",
        twitter = "awakencafe",
        ig = None,
    ),

    CCS(
        ccid = "ccpWdIrch6s-",
        name = "Dana Street Roasting Company",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/dana-street-roasting-mountain-view",
        address = "744 W Dana St Mountain View, CA 94041",
        url = "http://www.danastreetroasting.com",
        ig = None,
    ),

    CCS(
        ccid = "cc0WdKeIMBs2",
        name = "Heart Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/heart-portland-5",
        address = "537 SW 12th Ave Portland, OR 97205",
        url = "http://www.heartroasters.com/",
        ig = "heartroasters",
        twitter = "heartroasters",
    ),

    CCS(
        ccid = "ccnIEhpSAzv2",
        name = "Barista PDX",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/barista-portland-5",
        address = "529 SW 3rd Ave #110 Portland, OR 97204",
        url = "http://baristapdx.com/",
        ig = "baristapdx",
        twitter = "baristapdx",
    ),

    CCS(
        ccid = "ccQbcwYTrZ0F",
        name = "Public Domain",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/public-domain-coffee-portland",
        address = "603 SW Broadway Portland, OR 97205",
        url = "http://www.publicdomaincoffee.com/",
        twitter = "pdcoffee",
        ig = "publicdomaincoffee",
    ),

    CCS(
        ccid = "cc3o-xvW2kOw",
        name = "The Rose Establishment",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-rose-establishment-salt-lake-city",
        address = "235 400 W Salt Lake City, UT 84101",
        url = "http://www.theroseestb.com/",
        ig = "theroseestb",
        twitter = "TheRoseEstb",
        food = "cafe",
    ),

    CCS(
        ccid = "ccCYs7j0IkK4",
        name = "Wild Flour Bakery",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/wild-flour-bakery-banff",
        address = "211 Bear Street #101, Banff, AB T1L, Canada",
        url = "http://www.wildflourbakery.ca",
        ig = "wildflourbanff",
        twitter = "wildflourbanff",
        food = "meals",
    ),

    CCS(
        ccid = "ccW_cdB1HQc2",
        name = "Joe Coffee",
        location = "West Village",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/joe-coffee-new-york-4",
        address = "141 waverly place, new york, ny 10014",
        url = "http://www.joenewyork.com/",
        twitter = "joecoffeenyc",
        ig = None,
    ),

    CCS(
        ccid = "ccWGV7tHGGSk",
        name = "Cafe Grumpy",
        location = "Grand Central Terminal",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/cafe-grumpy-new-york-8",
        address = "89 EAST 42ND STREET, LEXINGTON PASSAGE, NEW YORK, NY 10017",
        url = "http://cafegrumpy.com",
        ig = "cafegrumpy",
        twitter = "cafegrumpy",
    ),

    CCS(
        ccid = "ccc7eRqCYZAn",
        name = "Voyageur du Temps",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/voyageur-du-temps-los-altos",
        address = "288 1st St, Los Altos, CA 94022",
        url = "http://www.voyageur.com",
        ig = "voyageurcafe",
        twitter = "voyageurcafe",
        food = "cafe",
    ),

    CCS(
        ccid = "cc_909hSV7nT",
        name = "Red Berry Coffee Bar",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/red-berry-coffee-bar-los-altos",
        address = "145 Main St Los Altos, CA 94022",
        url = "http://www.redberrycoffeebar.com",
        ig = "redberrycoffeebar",
        twitter = "redberrycb",
    ),

    CCS(
        ccid = "ccP1bKbH9WRM",
        name = "Toby's Estate Coffee & Tea",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/tobys-estate-chippendale",
        address = "32-36 City Rd Chippendale NSW 2008 Australia",
        url = "http://www.tobysestate.com.au/",
        ig = "tobysestatecoffee",
        twitter = "tobysestate",
    ),

    CCS(
        ccid = "cc4EkKx8Cxav",
        name = "Toby's Estate",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/tobys-estate-coffee-bondi-junction",
        address = "480-500 Oxford Street, Bondi Junction NSW 2022 Australia",
        url = "http://www.tobysestate.com.au/",
        ig = "tobysestatecoffee",
        twitter = "tobysestate",
    ),

    CCS(
        ccid = "ccm734N5eyGj",
        name = "Workshop Espresso",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/workshop-espresso-sydney",
        address = "500 George St The Galeries Sydney NSW 2000 Australia",
        url = None,
        ig = None,
    ),

    CCS(
        ccid = "ccMwJMRfVyH1",
        name = "Campos Coffee",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/campos-coffee-newtown",
        address = "193 Missenden Rd Newtown NSW 2042 Australia",
        url = "http://www.camposcoffee.com/",
        twitter = "camposcoffee",
        ig = None,
    ),

    CCS(
        ccid = "ccijNQ5BRF82",
        name = "The Cove Dining Co",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-cove-dining-abbotsford",
        address = "378 Great North Road Abbotsford NSW 2046 Australia",
        url = "http://www.thecovediningco.com.au/",
        ig = "thecovediningco",
    ),

    CCS(
        ccid = "ccavkk8gJJib",
        name = "Lyons R.A.W. Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/lyons-r-a-w-drummoyne",
        address = "155 Lyons Rd Drummoyne NSW 2047 Australia",
        url = None,
        ig = "lyonsraw",
    ),

    CCS(
        ccid = "ccm8Y-aEaj06",
        name = "Sonoma Bakery Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/sonoma-bakery-glebe",
        address = "215A Glebe Point Rd Glebe NSW 2037 Australia",
        url = "http://sonoma.com.au",
        ig = None,
    ),

    CCS(
        ccid = "ccn9y-UimOIH",
        name = "Sonoma Bakery Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/sonoma-bakery-cafe-waterloo-waterloo",
        address = "2/9-15 Danks St Waterloo NSW 2017 Australia",
        url = "http://sonoma.com.au",
        ig = None,
    ),

    CCS(
        ccid = "cc-EERnL-G0E",
        name = "Sonoma Bakery Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/sonoma-bakery-cafe-alexandria-alexandria",
        address = "32/44 Birmingham St Alexandria NSW 2015 Australia",
        url = "http://sonoma.com.au",
        ig = None,
    ),

    CCS(
        ccid = "cclOqEG7Ik-A",
        name = "Sonoma Bakery Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/sonoma-woollahra-woollahra",
        address = "5/156 Edgecliff Rd Woollahra NSW 2025 Australia",
        url = "http://sonoma.com.au",
        ig = None,
    ),

    CCS(
        ccid = "cckJlh-dw_gg",
        name = "Big Brekky",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/big-brekky-petersham",
        address = "316 Stanmore Rd Petersham NSW 2049 Australia",
        url = "http://bigbrekky.com.au/",
        ig = None,
    ),

    CCS(
        ccid = "ccpUbwGUZS7L",
        name = "Brewing Now",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/brewing-now-kingsford",
        address = "Shop 1/343 Anzac Parade Kingsford Sydney NSW 2032 Australia",
        url = None,
        ig = None,
    ),

    CCS(
        ccid = "ccYMbRP1NOAj",
        name = "Fresh Ground",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/fresh-ground-sandwiches-and-espresso-randwick",
        address = "154 Belmore Rd Randwick NSW 2031 Australia",
        url = None,
        ig = None,
    ),

    CCS(
        ccid = "ccW0_ItsM5jI",
        name = "Cafe Brioso (Coffee Cart)",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/cafe-brioso-kensington",
        address = "Library Lawn UNSW Kensington NSW 2033 Australia",
        url = None,
        ig = None,
    ),

    CCS(
        ccid = "cc3vp9mKTXCD",
        name = "The Gentlemen Baristas",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-gentlemen-baristas-london",
        address = "63 Union St London SE1 1SG United Kingdom",
        url = "http://thegentlemenbaristas.com/",
        twitter = "TheGBswhatwhat",
        ig = "thegentlemenbaristas",
    ),

    CCS(
        ccid = "ccmdpXUQr9Cp",
        name = "The Table Cafe",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/the-table-london-2",
        address = "83 Southwark St London SE1 0HX United Kingdom",
        url = "http://thetablecafe.com/",
        twitter = "thetablecafe",
        ig = "thetablecafe",
    ),

    CCS(
        ccid = "ccw-CYnwjCin",
        name = "Lonsdale Street Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/lonsdale-street-roasters-braddon",
        address = "7 Lonsdale St Braddon ACT 2612 Australia",
        url = "http://lonsdalestreetroasters.com/",
        twitter = "LSRoasters",
        ig = "lonsdalestreetroasters",
    ),

    CCS(
        ccid = "cccUT7Wv1UgF",
        name = "Nelson the Seagull",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/nelson-the-seagull-vancouver",
        address = "315 Carrall Street Vancouver, BC V6A 0A7 Canada",
        url = "http://www.nelsontheseagull.com/",
        twitter = "gastownseagull",
        ig = "nelsontheseagull",
    ),

    CCS(
        ccid = "cc5z1VMv44C5",
        name = "Pallet Coffee Roasters",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/pallet-coffee-roasters-vancouver",
        address = "323 Semlin Dr, Vancouver, BC V5L, Canada",
        url = "http://www.palletcoffeeroasters.com/",
        twitter = "palletcoffee",
        ig = "palletcoffee",
    ),

    CCS(
        ccid = "ccmFxQ97zZQP",
        name = "Arturo's Underground Cafe",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/arturos-underground-cafe-austin-2",
        address = "314 W 17th St, Austin, TX 78701",
    ),

    CCS(
        ccid = "ccwwTCzd9qa2",
        name = "House Cafe",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/house-cafe-austin",
        address = "2105 San Antonio St, Austin, TX 78705",
        url = "housecafeaustin.com",
    ),

    CCS(
        ccid = "ccV8fyRXA-WC",
        name = "Bru",
        rating = "unverified",
        yelp = "http://www.yelp.com/biz/bru-austin",
        address = "1301 Rio Grande, Austin, TX 78701",
        url = "bruaustin.com",
    ),

    CCS(
        ccid = "cctC2SBU5L8m",
        name = "Craftsman and Wolves Pacific",
        rating = "cromulent",
        yelp = "http://www.yelp.com/biz/craftsman-and-wolves-san-francisco-5",
        address = "1643 Pacific Avenue, San Francisco, CA 94109",
        url = "http://www.craftsman-wolves.com",
        ig = "craftsmanwolves",
        twitter = "craftsmanwolves",
    ),

]

## Translation table for @ names in various services

CCATDB = [
    {'twitter': '', 'ig': u'@fiddlerscoffee'},
    {'twitter': '', 'ig': u'@calipressjuice'},
    {'twitter': '', 'ig': u'@chansbros'},
    {'twitter': '', 'ig': u'@terarosacoffee'},
    {'twitter': '', 'ig': u'@herkimercoffee'},
    {'twitter': '', 'ig': u'@habitualcoffee'},
    {'twitter': '', 'ig': u'@overt_denver'},
    {'twitter': '', 'ig': u'@stumptowncoffee'},
    {'twitter': '', 'ig': u'@hacoffeebar'},
    {'twitter': '', 'ig': u'@vertigocoffeeroasters'},
    {'twitter': '', 'ig': u'@latteartgram'},
    {'twitter': '', 'ig': u'@brew_coffeeandbeer'},
    {'twitter': '', 'ig': u'@blacktoastcafe'},
    {'twitter': '', 'ig': u'@pabloandrustys'},
    {'twitter': '', 'ig': u'@7seedscoffee'},
    {'twitter': '', 'ig': u'@thelittlemarionette'},
    {'twitter': '', 'ig': u'@littlegremlincoffee'},
    {'twitter': '', 'ig': u'@porchandparlour'},
    {'twitter': '', 'ig': u'@fiftyfiftysf'},
    {'twitter': '', 'ig': u'@abbottstespresso'},
    {'twitter': '', 'ig': u'@single_o'},
    {'twitter': '', 'ig': u'@thecurator_'},
    {'twitter': '', 'ig': u'@oregan_coffee'},
    {'twitter': '', 'ig': u'@extractocoffee'},
    {'twitter': '', 'ig': u'@coffeebarredding'},
    {'twitter': '', 'ig': u'@blackeyecoffee'},
    {'twitter': '', 'ig': u'@revolverespresso'},
    {'twitter': '', 'ig': u'@case_coffee_roasters'},
    {'twitter': '', 'ig': u'@yardstickcoffee'},
    {'twitter': '', 'ig': u'@troublecoffeeco'},
    {'twitter': '', 'ig': u'@wanderinggoatcoffee'},
    {'twitter': '', 'ig': u'@lussolab_samchung'},
    {'twitter': '', 'ig': u'@tailor_coffee'},
    {'twitter': '', 'ig': u'@madaynecoffee'},
    {'twitter': '', 'ig': u'@threewilliamscafe'},
    {'twitter': '', 'ig': u'@tocofresh'},
    {'twitter': '', 'ig': u'@saintsimoncoffee'},
    {'twitter': '', 'ig': u'@vervecoffee'},

    {'twitter': 'commissaryLA', 'ig': u'@coffeecommissary'},
    {'twitter': 'BalconiCoffee', 'ig': u'@balconicoffee'},
    {'twitter': 'CafeDemitasse', 'ig': u'@cafe_demitasse'},
    {'twitter': 'KreuzbergCa', 'ig': '@kreuzbergcalifornia'},
    {'twitter': 'happygirl_co', 'ig': "@happygirlkitchen"},
    {'twitter': 'dinosaur_coffee', 'ig': u'@dinosaur_coffee'},
    {'twitter': 'TOMS', 'ig': u'@toms'},
    {'twitter': 'KeepCup', 'ig': u'@keepcup'},
    {'twitter': 'sodhousebakery', 'ig': u'@sodhousebakery'},
    {'twitter': 'facebook', 'ig': u'@facebook'},
    {'twitter': 'slipstreamdc', 'ig': u'@slipstreamdc'},
    {'twitter': 'NickCho', 'ig': u'@nickcho_'},

    # No twitter handle
    {'twitter': '#CoffeeCoffeeLA', 'ig': u'@coffeecoffeela'},
    {'tet': '#OtusThaiKitchen', 'ig': u'@otus_thaikitchen'},
    {'text': 'TOMS flagship', 'ig': u'@tomsflagship'},
    {'text': 'DeLise SF', 'ig': u'@DeLiseSF'}, # doesn't have one??
    {'text': 'Bright Coffee', 'ig': u'@brightcoffeeca'},
    {'text': 'Westfield', 'ig': u'@westfieldsyd'},
    {'text': 'Spearhead Coffee', 'ig': u'@spearheadcoffee'},

    ]

def at_translate(from_name, from_svc, to_svc, prefix = "@"):

    # accept prefixed or non-prefixed names
    from_name2 = from_name
    if (from_name2[0] == "@"):
        from_name2 = from_name2[1:]

    to_name = None
    dbs = [CCDB, CCATDB]

    for db in dbs:
        # search the db
        for e in db:
            if ((from_svc in e)
                and ((e[from_svc] == from_name)
                     or (e[from_svc] == from_name2))
                and (to_svc in e)):
                to_name = e[to_svc]
                break

        # return if valid
        if ((to_name is not None)
            and (to_name != "")):
            return prefix + to_name
    
    return None

###
##  database generation
#
def geojson_generate():

    fl = open(options['output'], "w")

    # build the list of ccs
    ccdb = []
    for ccs in CCDB:
        cc = ParseCCS(ccs)
        ccdb.append(cc)

    # now incorporate the insta list
    js = read_insta_db()
    
    for j in js:
        m = find_closest_ccs(j, ccdb)

        if (m is None):
            ccdb.append(InstaCC(j))
        else:
            InstaUpdate(m, j)

            # dump a warning if the two entries are bad
            disagreement(j, m)
            
    # build the geojson feature list from the DB
    features = []
    for cc in ccdb:
        features.append(ccs2geojson(cc))

        
    # build the master geojson data structure
    geojson = {"type": "FeatureCollection",
               "features": features}
    
    # dump the db
    fl.write(json.dumps(geojson,
                        indent=4, separators=(',', ': ')))

    print "Processed %d locations" % len(features)

###
##  check instagram data
#

def get_dst(lat, lng, ccs):

    lng2 = ccs[LATLONG][0]
    lat2 = ccs[LATLONG][1]

    dst = math.sqrt((lat2 - lat) ** 2 + (lng2 - lng) ** 2)

    return dst

def find_closest_ccs(i, ccl):

    lat = i["location"]["latitude"]
    lng = i["location"]["longitude"]
    
    min_dst = 10000000000
    min_ccl = None

    for cc in ccl:
        dst = get_dst(lat, lng, cc)

        if (dst < min_dst):
            min_dst = dst
            min_ccl = cc

    # FIXME: min threshold units?
    if (min_dst > 0.001):
        return None
    
    return min_ccl

def read_insta_db():
    # xxx: hard coded name
    try:
        fl = open("insta-posts.json")
    except:
        # do nothing if we can't open the file
        print "WARNING: instagram data not found"
        return []

    # parse the json
    s = ""
    for l in fl.readlines():
        s += l

    return json.loads(s)

# check if the insta data and the
# ccdb disagree. eg. if IG is cromulent and ccdb unverified
def disagreement(j, m):

    # Validate a rating inversion
    if ((j["rating"] == "cromulent")
        and (m["rating"] == "unverified")):
        print "WARN: %s has a rating disagreement" % m["name"]
        return True

    return False

def insta_check():
    js = read_insta_db()
    
    # Setup the CCDB
    ccl = []
    for ccs in CCDB:
        ccl.append(ParseCCS(ccs))

    # XXX: slow search
    # for each insta item
    unmatched = []
    matched = []
    disagreeing = []
    for j in js:
        m = find_closest_ccs(j, ccl)

        if (m is None):
            unmatched.append(j)
        else:
            matched.append(j)

            if (disagreement(j, m)):
                disagreeing.append(j)

    print "%d matched, %d unmatched, %d disagreeing" % (len(matched), len(unmatched), len(disagreeing))

###
##  ccid generation
#

# prefix for ids in the database
CCID_PREFIX = "cc"

# prefix for IDs in the insta-find locations
CCIG_PREFIX = "ig"

# list of characters for IDs -- 52 + 10 + 2 = 64
IDCHARS = string.ascii_letters + string.digits + "-_"

# 10 chars of 4 bit = big number
IDLEN = 10

def get_rand_idnum():
    # gonna make a random
    random.seed()
    
    return random.randint(0, len(IDCHARS) ** IDLEN)


def num_to_id(num):

    if (num <= 0):
        raise RuntimeError("invalid id %d" % num)
        
    id = ""
    while(num > 0):
        id += IDCHARS[num % len(IDCHARS)]
        num /= len(IDCHARS)

    return id
        
def mkid():
    n = get_rand_idnum()

    id = num_to_id(n)
    
    return id

def genid(prefix):

    id = mkid()
    return "%s%s" % (prefix, id)

def idgen():
    # generate a new id
    id = genid(CCID_PREFIX)

    print 'ccid = "%s"' % id

###
##  ccid fixup
#

# This is kinda gross. First, run through the CCDB list, generating a
# list of entries that do not contain a 'ccid'. Then, walk through
# this script file finding 'CCS' entries and adding new IDs to
# this. Currently we expect "CCS(" lines as above. This could very
# well corrupt this script. Isn't that what version control is for?

CCSTOK = "CCS("

def ccid_fixup():

    fixups = 0
    
    # search the db for items without a ccid
    # and add them to a list
    idxlist = []
    for n in range(len(CCDB)):
        if ("ccid" not in CCDB[n]):
            idxlist.append(n)

    if (len(idxlist) == 0):
        print "All CCDB entries have ids. Nothing to fixup"
        return
    
    # crack open ourselves and search for "CCS(" lines
    idx = 0
    fl = open(__file__, "r")
    outbuf = ""
    for ln in fl.readlines():
        # buffer line to output verbatim
        outbuf += ln

        # see if we should inject some magic
        sln = ln.strip()
        if (sln == CCSTOK):

            # if we need to fix up this CCS
            if(idx in idxlist):
                # keep the same indentation, with a tab
                indent = ln[:ln.find(CCSTOK)] * 2
                
                # make a line of it
                outbuf += (indent + 'ccid = "%s",\n' % genid(CCID_PREFIX))

                # accounting is fun
                fixups += 1
                
            # move onto next CCS
            idx += 1


    #yolo
    fl = open(__file__, "w")
    fl.write(outbuf)

    print "Fixed up %d entries" % fixups

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
        db_stat(ccs, invs, "Invalid fields/values specified", db_errors)
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

    parser.add_argument("--instacheck", dest="action", action="store_const",
                        const="instacheck", help="check instagram data")

    parser.add_argument("--output", dest="output", nargs=1,
                        help="output file for --geojson, default = 'ccgeo.json'",
                        default="ccgeo.json")

    parser.add_argument("--idgen", dest="action", action="store_const",
                        const="idgen",
                        help="generate a random ccid")
    
    parser.add_argument("--idfixup", dest="action", action="store_const",
                        const="idfixup",
                        help="update the script file with new ccids for entries that don't have them. Please commit your changes before running this.")
    
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
    elif (action == "instacheck"):
        insta_check()
    elif(action == "geojson"):
        geojson_generate()
        geocache_save()
    elif(action == "idgen"):
        idgen()
    elif(action == "idfixup"):
        ccid_fixup()
    else:
        raise RuntimeError("unknown action '%s'" % action)
        

#!/usr/bin/python

import urllib
import json
import sys

## Pull down a list of places by their location and
## save it out. ccdb will combine them after the fact.

## @cromulentcoffee
CCUID = 1993210575

## The magic access token for Insta-api
access_token = None

###
##  Class representing an Instagram location
#

class InstaLoc:
    def __init__(self, locid, rating, locinfo):
        self.posts = []
        self.locid = locid
        self.locinfo = locinfo
        self.rating = rating

    def add_post(self, post):
        self.posts.append(post)

    def get_rep(self):
        return { "location" : self.locinfo,
                 "rating": self.rating,
                 "posts" : self.posts }
    
###
##  Insta-json
#

# reduce a Insta JSON blob to what we care about
def img2cache(ii):
    d = {}
    
    d["link"] = ii["link"]
    d["thumb"] = ii["images"]["thumbnail"]

    locid = None
    if (ii["location"] is not None):
        # some of the data is really shitty...
        if ("id" not in ii["location"]):
            print "id on %s missing in location?" % d["link"]
        elif ("latitude" not in ii["location"]):
            print "lat on %s missing in location?" % d["link"]
        elif ("longitude" not in ii["location"]):
            print "lng on %s missing in location?" % d["link"]
        else:
            locid = ii["location"]["id"]
            
        
    return (locid, d)

# extract the location deets from an image blob
def img2locinfo(ii):
    l = ii["location"]
    
    return l

    
###
##  Talk http/json
#

def http_get_js(url):

    # pull a file
    nw = urllib.urlopen(url)

    # read it
    s = ""
    for line in nw.readlines():
        s += line

    # parse it
    js = json.loads(s)

    return js

###
##  Pulling the post list
#

def get_list_by_url(url, rating):
    
    # list of posted items
    pl = {}

    # total and location-tagged counters
    tcount = 0
    lcount = 0
    
    # loop over the pages
    while (url is not None):
        # pull the first page
        js = http_get_js(url)

        # Decode the returned list
        ds = js["data"]
        for d in ds:
            tcount += 1
            try:
                (k, v) = img2cache(d)
            except:
                print d
                sys.exit(1)

            # untagged post 
            if (k is None):
                continue

            lcount += 1
            
            # first post in location
            if (k not in pl.keys()):
                pl[k] = InstaLoc(k, rating, img2locinfo(d))

            pl[k].add_post(v)
            
        # get the next list
        url = None
        pag = js['pagination']
        if ("next_url" in pag):
            url = pag['next_url']

    print "Found %d posts, %d with locations" % (tcount, lcount)
            
    return pl

    
def get_post_list():

    # base URL of our most recent posts
    url = "https://api.instagram.com/v1/users/%s/media/recent?access_token=%s" % (CCUID, access_token)

    return get_list_by_url(url, "cromulent")
    
def get_like_list():
    
    # base URL of our likes
    url = "https://api.instagram.com/v1/users/self/media/liked?access_token=%s" % access_token

    return get_list_by_url(url, "insta-find")

    
###
##  Entrypoint
#

def usage():
    print "usage: %s <auth-token>" % sys.argv[0]
    sys.exit(1)

if (__name__ == "__main__"):

    if (len(sys.argv) <= 1):
        usage()
        
    # This needs to be gotten live
    access_token = sys.argv[1]

    # Pull the list of #cc postings
    print "Pulling post list..."
    post_list = get_post_list()

    # Pull the list of #cc likes
    print "Pulling like list..."
    like_list = get_like_list()
    
    # Translate that to something we want to save
    sl = []
    
    for p in post_list.keys():
        j = post_list[p].get_rep()
        sl.append(j)

    for l in like_list.keys():
        j = like_list[l].get_rep()
        sl.append(j)

    # save it
    fl = open("insta-posts.json", "w")
    fl.write(json.dumps(sl,
                        indent=4, separators=(',', ': ')))

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
    def __init__(self, locid, locinfo):
        self.posts = []
        self.locid = locid
        self.locinfo = locinfo

    def add_post(self, post):
        self.posts.append(post)

    def get_rep(self):
        return { "location" : self.locinfo,
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
        locid = ii["location"]["id"]
        
    return (locid, d)

# extract the location deets from an image blob
def img2locinfo(ii):
    l = ii["location"]
    
    return ii["location"]

    
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

def get_post_list():

    # list of posted items
    pl = {}
    
    # base URL of our most recent posts
    url = "https://api.instagram.com/v1/users/%s/media/recent?access_token=%s" % (CCUID, access_token)

    # loop over the pages
    while (url is not None):
        # pull the first page
        js = http_get_js(url)

        # Decode the returned list
        ds = js["data"]
        for d in ds:
            (k, v) = img2cache(d)

            # untagged post 
            if (k is None):
                continue

            # first post in location
            if (k not in pl.keys()):
                pl[k] = InstaLoc(k, img2locinfo(d))

            pl[k].add_post(v)
            
        # get the next list
        url = None
        pag = js['pagination']
        if ("next_url" in pag):
            url = pag['next_url']

    return pl

###
##  Entrypoint
#

if (__name__ == "__main__"):

    # This needs to be gotten live
    access_token = sys.argv[1]

    # Pull the list of #cc postings
    post_list = get_post_list()
    
    # Translate that to something we want to save
    sl = []
    for p in post_list.keys():
        j = post_list[p].get_rep()
        sl.append(j)

    # save it
    fl = open("insta-posts.json", "w")
    fl.write(json.dumps(sl,
                        indent=4, separators=(',', ': ')))

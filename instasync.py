#!/usr/bin/python

import credentials
import urllib
import json
import sys
import re

## Pull down a list of places by their location and
## save it out. ccdb will combine them after the fact.

## @cromulentcoffee
CCUID = 1993210575

## The magic access token for Insta-api
access_token = None

###
##  Managing the pending list of tweets
#

PENDING_FILE = "pending-posts.json"

def new_pending_post_list():

    np = {}

    # the most recent timestamp of a post we've made
    np["newest-post"] = 0

    # list of pending posts to tweet
    np["pending-tweets"] = []

    return np

def read_pending_post_list(make_new = True):

    try:
        fl = open(PENDING_FILE)
        pending = json.load(fl)
    except:
        print "Error reading pending post list, starting fresh"
        if (make_new):
            pending = new_pending_post_list()
        else:
            pending = None

    return pending

def update_pending_post_list(pending, post):

    ctime = int(post["created_time"])
    if (ctime <= pending["newest-post"]):
        # already seen image
        return

    # track the highest number we've seen for next time
    if (pending.get("next-newest-post", ctime) <= ctime):
        pending["next-newest-post"] = ctime

    # make a list record and add it to the top of the list
    # pending["pending-tweets"].append(post["link"])
    pending["pending-tweets"].insert(0, post["link"])

def save_pending_post_list(pending):

    # check if we updated the timestamp
    if (pending.get("next-newest-post") is not None):
        pending["newest-post"] = pending["next-newest-post"]
        del pending["next-newest-post"]

    # write the file
    fl = open(PENDING_FILE, "w")
    fl.write(json.dumps(pending,
                        indent=4, separators=(',', ': ')))

    print "%d pending tweets" % len(pending["pending-tweets"])

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
            # print "id on %s missing in location?" % d["link"]
            pass
        elif ("latitude" not in ii["location"]):
            # print "lat on %s missing in location?" % d["link"]
            pass
        elif ("longitude" not in ii["location"]):
            # print "lng on %s missing in location?" % d["link"]
            pass
        else:
            locid = ii["location"]["id"]
            
        
    return (locid, d)

# extract the location deets from an image blob
def img2locinfo(ii):
    l = ii["location"]
    
    return l

###
##  name decoding
#

NAME_RE = "(@[a-zA-Z0-9_]+)(.*)"
HASH_RE = "(#[^.?:/\#!@#$%^&*\(\)]+)(.*)"

def parse_token(prefix, regex, tok):

    # pass through other words
    if (tok[0] != prefix):
        return (False, None, None)

    # regex into the name and the suffix
    m = re.search(regex, tok)

    if (m is None):
        print tok

    igname = m.group(1)
    suffix = m.group(2) # empty string if no suffix

    return (True, igname, suffix)

def parse_name(tok):

    return parse_token("@", NAME_RE, tok)

###
##  stats
#

class Stats:
    def __init__(self):
        self.ht_list = {}
        self.at_list = {}

    def add_ht(self, ht):
        self.ht_list[ht] = self.ht_list.get(ht, 0) + 1

    def add_at(self, at):
        self.at_list[at] = self.at_list.get(at, 0) + 1

stats = Stats()

def add_to_stats(d):
    t = d["caption"]["text"]

    toks = t.split()

    for tok in toks:
        (is_ht, name, suffix) = parse_token("#", HASH_RE, tok)

        if (is_ht):
            stats.add_ht(name)
            continue
    
        (is_at, name, suffix) = parse_name(tok)

        if (is_at):
            stats.add_at(name)
            continue

## debug
def print_at_list():

    l = []
    for k in stats.at_list:
        d = { "ig": k,
              "twitter" : "" }
        l.append(d)

    print l

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
##  Pulling posts and the post list
#

def get_list_by_url(url, rating, pending, stats):
    
    # list of posted items
    pl = {}

    # total and location-tagged counters
    tcount = 0
    lcount = 0
    
    # loop over the pages
    while (url is not None):
        # pull the first page
        js = http_get_js(url)

        # inform the user
        # print ".",
        sys.stdout.write(".")
        sys.stdout.flush()

        # Decode the returned list
        print js
        ds = js[u"data"]
        for d in ds:
            tcount += 1

            # deal with pending tweets
            if (pending is not None):
                update_pending_post_list(pending, d)

            # maybe collect stats
            if (stats):
                add_to_stats(d)

            # turn into a short form
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

    print
    print "Found %d posts, %d with locations" % (tcount, lcount)
            
    return pl

    
def get_post_list(pending):

    check_access_token()

    # base URL of our most recent posts
    url = "https://api.instagram.com/v1/users/%s/media/recent?access_token=%s" % (CCUID, access_token)

    return get_list_by_url(url, "cromulent", pending, True)
    
def get_like_list():

    check_access_token()
    
    # base URL of our likes
    url = "https://api.instagram.com/v1/users/self/media/liked?access_token=%s" % access_token

    return get_list_by_url(url, "insta-find", None, False)

def get_post_by_url(post):

    check_access_token()

    toks = post.split("/")
    shortcode = toks[-2]

    # URL of the media object
    url = "https://api.instagram.com/v1/media/shortcode/%s?access_token=%s" % (shortcode, access_token)

    # pull it down
    js = http_get_js(url)

    return js["data"]

###
##  credentials
#

def read_access_token():    

    global access_token

    # FIXME: embiggen the access token type we use
    cred = credentials.get_credentials("ig")
    if (cred is None):
        print "Could not credentials in file %s. See credentials.py" % credentials.CCAUTH
        sys.exit(1)
    if ("auth-token" not in cred):
        print "Could not find auth-toke in ig credentials. See credentials.py"
        sys.exit(1)
    access_token = cred["auth-token"]

def check_access_token():

    if (access_token is None):
        read_access_token()


###
##  Entrypoint
#

def usage():
    print "usage: %s" % sys.argv[0]
    sys.exit(1)

if (__name__ == "__main__"):

    if (len(sys.argv) != 1):
        usage()
        
    # pull our credentials
    read_access_token()

    # get the list of pending posts
    pending = read_pending_post_list()

    # Pull the list of #cc postings
    print "Pulling post list..."
    post_list = get_post_list(pending)

    # XXX: fixme
    # dump the at list
    # print_at_list()

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

    # and the pending posts
    save_pending_post_list(pending)


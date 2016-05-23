#!/usr/bin/python

###
##  twitter access for #cc
#

import sys
import ccdb
import tweepy
import urllib
import tempfile
import instasync
import credentials

###
##  actual tweeting
#

def get_api():
    # pull the credentials
    cred = credentials.get_credentials("twitter")
    if (cred is None):
        print "%s not found / missing twitter credentials" % credentials.CCAUTH

    # connect to twitter
    auth = tweepy.OAuthHandler(cred["cons-key"], cred["cons-secret"])
    auth.set_access_token(cred["access-token"], cred["access-secret"])

    api = tweepy.API(auth)

    return api

def url2tmpfile(url):

    # make a temp file
    fl = tempfile.NamedTemporaryFile(suffix=".jpg")

    # get a file-like object to the source image
    nw = urllib.urlopen(t.imgurl)

    fl.write(nw.read())

    print "file: %s" % fl.name

    return (fl.name, fl)

def post_tweet(t):

    # cache the image
    (fname, fl) = url2tmpfile(t.imgurl)

    # create a session
    api = get_api()
    
    # post it
    r = api.update_with_media(fname, t.tweet)

    # print r

    s = r.id
    print "Tweet URL: https://twitter.com/cromulentcoffee/status/%s" % s

    return True

###
##  name translation
#
def at_xlat(tok):

    # pull apart the name
    (is_name, igname, suffix) = instasync.parse_name(tok)

    if (not is_name):
        return tok

    twittername = ccdb.at_translate(igname, "ig", "twitter")

    if (twittername is None):
        # fallback if they don't have a twitter account
        twittername = ccdb.at_translate(igname, "ig", "text", "")

    if (twittername is None):
        return None

    return twittername + suffix

###
##  caption generation
#

CC_HASHTAGS = ["#cappuccino", "#latte", "#gibraltar",
               "#cortado", "#espresso"
               "#latteart", "#coffee",
               "#sanfrancisco", "#newyork", "#pausalanewaycafe",
               "#brewedwithheart", "#washington", "#seoulfood"]

KILL_HASHTAGS = ["#coffeebreak", "#coffeelover", "#coffeetime",
                 "#coffeeaddict", "#caffeine", "#thanksgiving",
                 "#merrychristmas"]

def get_url_len():
    return 24 # XXX: FIXME: consult twitter for length

def get_media_len():
    return 24 # XXX: FIXME: consult twitter for length

TWEET_MAX = 140 - get_media_len()

# FIXME
def caption2tweet(cap, has_url):

    toks = cap.split()
    tmax = TWEET_MAX
    if (has_url):
        tmax -= get_url_len()
    backup_list = []
    good_list = []

    # run through the list and identify the shortest thing
    tweet = ""
    for tok in toks:
        if (tok in CC_HASHTAGS):
            backup_list.append(tok)
        elif (tok not in KILL_HASHTAGS):
            name = at_xlat(tok)
            if (name is None):
                print "Couldn't translate name '%s' to tweet" % tok
                return None
            tweet += name + " "

    # check the tweet size
    tlen = len(tweet)
    if (tlen > tmax):
        print "Tweet too long at %d: '%s' -- '%s'" % (tlen, ENC(tweet), ENC(cap))
        return None

    # now grab words as we go along
    for tok in backup_list:
        # skip words we already have
        if (tok not in backup_list):
            continue

        # if they fit, add words to the good list
        d = len(tok) + 1
        if ((tlen + d) <= tmax):
            good_list.append(tok)
            tlen += d

    # run through the list and identify the shortest thing
    tweet = ""
    for tok in toks:
        # skip the kill list
        if (tok in KILL_HASHTAGS):
            continue

        # skip hashtags not in the good list
        if ((tok in CC_HASHTAGS)
            and (tok not in good_list)):
            continue
        
        # add the word
        tweet += at_xlat(tok + " ")

    # kill the trailing space
    tweet = tweet.strip()

    return tweet

###
##  post object representation
#

def find_largest_image(ijs):

    size = 0
    imgurl = None
    for k in ijs:
        img = ijs[k]
        z = int(img["width"])
        if (z < size):
            continue
        imgurl = img["url"]
        size = z

    if (imgurl is None):
        raise RuntimeError("couldn't find an image?\n%s" % ijs)

    return imgurl

class PostObject():
    def __init__(self, js):
        self.locid = None
        if (("location" in js)
            and (js["location"] is not None)
            and ("id" in js["location"])):
            self.locid = js["location"]["id"]
        self.caption = js["caption"]["text"]
        self.imgurl = find_largest_image(js["images"])
        self.ccurl = None
        self.tweet = None

    def generate_tweet(self):
        # generate the URL portion
        has_url = True
        self.get_ccurl()
        if (self.ccurl is None):
            has_url = False

        # generate tweet text
        ttext = caption2tweet(self.caption, has_url)

        if (ttext is None):
            return 

        # append if we've gotten this far
        if (self.ccurl is None):
            if (len(ttext) > TWEET_MAX):
                raise RuntimeError("Generated oversized tweet!")
            self.tweet = ttext
        else:
            if ((len(ttext) + get_url_len()) > TWEET_MAX):
                raise RuntimeError("Generated oversized tweet with URL!")
            self.tweet = "%s %s" % (ttext, self.ccurl)

        return self.tweet

    def get_ccurl(self):
        if (self.locid is None):
            return

        # FIXME: we should really cross-check ccdb to ensure
        # this thing actually exists
        self.ccurl = "http://cromulentcoffee.com/?id=ig%s" % self.locid

        return self.ccurl

###
##  tweet generation
#

def make_tweet(p):

    # pull down the URL
    print "making tweet %s" % p

    d = instasync.get_post_by_url(p)

    # Make a more convenient object representation
    o = PostObject(d)

    # translate the caption
    o.generate_tweet()

    if (o.tweet is None):
        return None

    return o

###
##  argument parsing
#

VALID_ARGS = ["test", "post", "verify"]

def usage():
        print "usage: %s [test|post|verify]" % sys.argv[0]
        sys.exit(1)

def parse_args():

    if (len(sys.argv) == 1):
        return "test"

    if (len(sys.argv) > 2):
        usage()

    if (sys.argv[1] not in VALID_ARGS):
        usage()

    return sys.argv[1]

###
##  pipe fix-up
#

def ENC(x):
    return x.encode('utf-8')

###
##  entrypoint
#
if (__name__ == "__main__"):

    op = parse_args()

    # read the pending list
    pending = instasync.read_pending_post_list(False)

    if (pending is None):
        print "No pending list, exiting"
        sys.exit(1)

    # FIXME: read the handle translation table

    plist = pending["pending-tweets"]

    if (len(plist) == 0):
        print "No more tweets pending, exiting"
        sys.exit(0)

    # iterate over the pending list, trying to post
    good = 0
    skip = 0
    for i in range(0, len(plist)):
        p = plist[i]
        t = make_tweet(p)

        if (t is None):
            print "Can't tweet %s" % p
            skip + 1
            continue
        
        print "Can tweet %s: %s (%d)" % (ENC(p), ENC(t.tweet), len(t.tweet))
        good += 1

        # bail if we can print something
        if (op == "test"):
            print "Found a valid tweet after %d skips" % skip
            sys.exit(1)

        # do a post
        if (op == "post"):
            # post the tweet
            r = post_tweet(t)
            if (r):
                del plist[i]
                instasync.save_pending_post_list(pending)
                sys.exit(0)
            else:
                sys.exit(1)

        # fall through on "verify" to process all


    if (op == "verify"):
        print "Verification done. %d / %d postable" % (good, len(plist))
    else:
        print "No valid tweets to post"

#!/usr/bin/python

###
##  twitter access for #cc
#

import tweepy
import credentials

# pull the credentials
cred = credentials.get_credentials("twitter")
if (cred is None):
    print "%s not found / missing twitter credentials" % credentials.CCAUTH

# connect to twitter
auth = tweepy.OAuthHandler(cred["cons-key"], cred["cons-secret"])
auth.set_access_token(cred["access-token"], cred["access-secret"])

api = tweepy.API(auth)

public_tweets = api.home_timeline()
for tweet in public_tweets:
    print tweet.text



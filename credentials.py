#!/usr/bin/python

###
##  Manage user credentials for #cc operations
#

import json
import os

# json file with authetnication information for IG, twitter, etc.
CCAUTH = os.path.expanduser("~/.ccauth")

###
##  Reading
#

def get_all_credentials():
    try:
        fl = open(CCAUTH)

        cred = json.load(fl)
    except:
        return None

    return cred

def get_credentials(service):
    c = None
    cs = get_all_credentials()

    if cs is not None:
        c = cs.get(service)

    return c

###
##  Default template
#

def print_credential_template():

    # build a simple dict
    d = {}

    d["ig"] = { "auth-token" : "<auth-token>" }
    d["twitter"] = { "cons-key" : "<consumer-key>",
                     "cons-secret" : "<consumer-secret>",
                     "access-token" : "<access-token>",
                     "access-secret" : "<access-token-secret>" }
                  
    
    print json.dumps(d, indent=4, separators=(',', ': '))

###
##  Command-line test
#
if (__name__ == "__main__"):
    
    # read all the credentials
    cred = get_all_credentials()

    if (cred is None):
        print "Missing / unreadable credentials"
    else:
        if ("twitter" in cred):
            print "Twitter: %s" % cred["twitter"]

        if ("ig" in cred):
            print "Instagram: %s" % cred["ig"]

    print "Credential template:"
    print_credential_template()


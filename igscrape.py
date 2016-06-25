#!/usr/bin/python

import urllib
import json
import sys
import re

def http_get_url_lines(url):
    nw = urllib.urlopen(url)

    return nw.readlines() 

def http_get_url(url):

    # pull a file
    lines = http_get_url_lines(url)

    # read it
    s = ""
    for line in lines:
        s += line

    return s

START_TOK = " = {"
END_TOK = ";</script>"
def extract_line_json(line):

    start = line.find(START_TOK)
    end = line.rfind(END_TOK)
    
    line = line[start+len(START_TOK)-1:end]

    js = json.loads(line)

    return js
    
def scrape_ig_json_from_url(post):

    lines = http_get_url_lines(post)

    for line in lines:
        if ("window._sharedData" in line):
            return extract_line_json(line)

    return None


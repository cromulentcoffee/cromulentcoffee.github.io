# \#cromulentcoffee
================

\#cromulentcoffee database HTML google map UI

Display GeoJSON coffee shops, from a hand-curated database, and
scraped from the cromulent coffee instagram account feed.

## Dataflow
===========

* ccgeo.json is the current "release" database, consumed by cc.js on the webpage

* ccdb.py generates ccgeo.json from the CCDB database in ccdb.py and the insta-posts.json file

* insta-posts.json is generated from instasync.py


## Twitter APIs
===============

How to install "tweepy" for twitter scripts, on your Mac:

    % sudo easy_install pip
    ...
    % sudo easy_install tweepy
    ...

Should be all is necessary
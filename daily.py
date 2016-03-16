#!/bin/sh

echo "Pulling instagram data"
./instasync.py || exit 1

echo "Generating geojson file"
./ccdb.py --geojson || exit 1

echo "Making a tweet"
./tweet.py post || exit 1

echo "Commiting updates to repo"
git commit -a -m "Daily instasync & tweet post" || exit 1

echo "Pushing live"
git push origin HEAD || exit 1

echo "done"

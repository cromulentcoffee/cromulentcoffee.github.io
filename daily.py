#!/bin/sh

echo "[DAILY] Synching to master"
git pull || exit 1

echo "[DAILY] Pulling instagram data"
./instasync.py || exit 1

echo "[DAILY] Generating geojson file"
./ccdb.py --geojson || exit 1

echo "[DAILY] Making a tweet"
./tweet.py post || exit 1

echo "[DAILY] Commiting updates to repo"
git commit -a -m "[DAILY] Daily instasync & tweet post" || exit 1

echo "[DAILY] Pushing live"
git push origin HEAD || exit 1

echo "[DAILY] done"

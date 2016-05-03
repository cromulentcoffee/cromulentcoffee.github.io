#!/bin/sh

if [ -t 1 ] ; then
    echo "[DAILY] running in interactive (terminal) mode"
else
    echo "[DAILY] running in batch mode -- `date`"

    SCRIPT_PATH=`dirname $0`
    echo "[DAILY] moving current dir to $SCRIPT_PATH"
    cd $SCRIPT_PATH

    echo "[DAILY] waiting 30 sec for network to come up"
    sleep 30
    echo "[DAILY] that'll do?"
fi

exit 1

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

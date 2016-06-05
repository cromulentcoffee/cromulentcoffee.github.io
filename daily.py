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

    echo "[DAILY] making some pings"
    ping -c 5 google.com
    ping -c 5 github.com

    echo "[DAILY] that'll do?"

    echo "[DAILY] running caffeinate"
    caffeinate -u -t 600 &
fi

echo "[DAILY] Synching to master"
git pull || exit 1

echo "[DAILY] Skipping sync while we're sandboxed"

# echo "[DAILY] Pulling instagram data -- `date`"
# ./instasync.py || exit 1

# echo "[DAILY] Generating geojson file -- `date`"
# ./ccdb.py --geojson || exit 1

echo "[DAILY] Making a tweet"
./tweet.py post || exit 1

echo "[DAILY] Commiting updates to repo"
git commit -a -m "[DAILY] Daily instasync & tweet post" || exit 1

echo "[DAILY] Pushing live"
git push origin HEAD || exit 1

echo "[DAILY] done"

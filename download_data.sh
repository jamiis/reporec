#!/bin/bash
#
# description:
#   fetches github database dump files from ghtorrent and loads them into mongo
#
# usage: ./download_trips.sh
#
# requirements: curl, mongodb, mongorestore
#
# author: jamis johnson
#

echo
echo "==================="
echo "Downloading Github watchers collections and loading into mongodb."
echo "NOTE: data is large and may take a long time depending on you connection."
echo "==================="
echo

# extract $1-number of latest watchers db dumps urls
urls=`
    curl http://ghtorrent.org/downloads.html | 
    grep tar.gz |
    cut -d'"' -f2 |
    grep -E "(watchers-)" |
    tail -n $1`

for url in $urls
do
    echo "==================="

    # download the db dump
    echo "Downloading: $url"
    curl -O $url

    # extract data dump from archive
    file=`basename $url`
    echo "Extracting: $file"
    tar -zxf $file

    # load dump/github/[watchers|repos].bson into mongo
    echo "Loading dump into mongo"
    mongorestore

    # remove gzipped tarball and mongo .bson data
    #rm $file
    rm -rf dump/
done

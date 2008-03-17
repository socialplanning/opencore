#!/bin/bash

if [ `hostname` != "flow" ]; then
  echo "This script is intended to be run on flow"
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: $0 SITE_PATH BUILD_PATH"
  exit 1
fi
SITE_PATH=$1

if [ -z "$2" ]; then
  echo "Usage: $0 SITE_PATH BUILD_PATH"
  exit 1
fi
BUILD_PATH=$2

ZEO_PATH=$SITE_PATH/var/zeo
ZODB_PATH=$ZEO_PATH/Data.fs
ZOPE_PATH=$BUILD_PATH/opencore/lib/zope

if [ ! -d $ZOPE_PATH ]; then
  echo "Error: directory $ZOPE_PATH does not exist"
  exit 1
fi

TOMORROW=$(date -d +1days +%Y-%m-%d)

echo "Restoring copy of live data to $ZODB_PATH..."

PYTHONPATH="$PYTHONPATH:$ZOPE_PATH/lib/python" \
  $ZOPE_PATH/bin/repozo.py --recover --date="$TOMORROW" \
    -o $ZODB_PATH \
    -r /backup/theman.openplans.org/repozo/nycstreets

echo "Done"

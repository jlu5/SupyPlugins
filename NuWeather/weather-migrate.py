#!/usr/bin/env python3
"""
Migrates user locations from the Weather plugin to NuWeather.
"""

import argparse
import sqlite3
import pickle

parser = argparse.ArgumentParser(prog='weather-migrate', description=__doc__)
parser.add_argument('infile', type=str, help='input filename (BOT_DATA_DIR/Weather.db)')
parser.add_argument('outfile', type=str, help='output filename (e.g. BOT_DATA_DIR/NuWeather.db)')
args = parser.parse_args()

conn = sqlite3.connect(args.infile)
c = conn.cursor()
# We only care about nick and location
c.execute('SELECT nick, location from users')
out = dict(c.fetchall())
print("OK read %d entries from %s" % (len(out), args.infile))
c.close()  # No need to commit since we only read

with open(args.outfile, 'wb') as outf:
    pickle.dump(out, outf)
    print("OK wrote output to %s" % args.outfile)

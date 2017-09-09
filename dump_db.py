#!/usr/bin/env python3

import sys

import plyvel

db = plyvel.DB(sys.argv[1], create_if_missing=False)
it = db.iterator()
for k, v in it:
	print(k, v)

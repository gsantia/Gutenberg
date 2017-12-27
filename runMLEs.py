#!/usr/bin/python
import os, sys, json

batchnum = sys.argv[1]

with open("batches.json") as f:
    batches = json.loads(f.read())

for booknum in batches[batchnum]:
    os.system("python2 MLE.py "+booknum)

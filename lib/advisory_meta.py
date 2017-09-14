#!/usr/bin/python
from __future__ import print_function
#import argparses
import json
from sys import argv, stderr

data=None
version=argv[2]
try:
    tree=argv[3]
except IndexError:
    tree='xen'
with open(argv[1], 'r') as f:
    data = json.load(f)

if version == 'trees':
    for t in data['Trees']:
        print(t)
elif version in data['SupportedVersions']:
    for p in data['Recipes'][version]['Recipes'][tree]['Patches']:
        print(p)
else:
    print(version, 'not supported', file=stderr)

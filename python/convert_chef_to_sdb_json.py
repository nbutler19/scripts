#!/usr/bin/env python

import simplejson as json
import sys

f = sys.stdin

contents = json.load(f)

newjson = {}

newjson['name'] = contents['id']
newjson['attributes'] = contents

array_wrapper = []

array_wrapper.append(newjson)

print json.dumps(array_wrapper, indent=True)

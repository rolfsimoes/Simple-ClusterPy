#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys

xmin, xmax = sys.argv[1].split('-')

xmin, xmax = int(xmin), int(xmax)

xsum = 0
x = xmin
while x <= xmax:
    xsum += x
    x += 1

print "Somatório (%d...%d) = %d" % (xmin, xmax, xsum)


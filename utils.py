#!/usr/bin/python
"""
    Author: Fabien Royer
    Copyright 2013-2015 Fabien Royer

    This file is part of the "Humble Roots Project" or "HRP".

    "HRP" is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    "HRP" is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with "HRP".  If not, see <http://www.gnu.org/licenses/>.
"""
from datetime import datetime
from urllib import urlencode
from urlparse import parse_qs
import inspect
import time
import socket

# Map a range of values to another (see: http://rosettacode.org/wiki/Map_range#Python)
def MapRange(range1, range2, value):
    (a1, a2), (b1, b2) = range1, range2
    return  b1 + ((value - a1) * (b2 - b1) / (a2 - a1))

# Print a time stamp
def GetTimeStamp():
    return str(datetime.now())

def GetSecondsSinceEpoch():
    return long(round(time.time()))

def UrlEncode(query):
    return urlencode(query, True)

def UrlDecode(qs):
    return parse_qs(qs, keep_blank_values=True, strict_parsing=True)

def GetStackInfo():
    callerframerecord = inspect.stack()[1]    # 0 represents this line
                                              # 1 represents line at caller
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    #print info.filename                       # __FILE__
    #print info.function                       # __FUNCTION__
    #print info.lineno                         # __LINE__
    return info

def WaitForInternetUp(hostname="www.google.com", port=443):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            sock.connect((hostname, port))
            break
        except socket.error as msg:
            print msg
            time.sleep(1)
        finally:
            sock.close()

if __name__ == '__main__':
    WaitForInternetUp()

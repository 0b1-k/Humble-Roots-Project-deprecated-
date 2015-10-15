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
from subprocess import call
from datetime import datetime
import SimpleHTTPServer
import SocketServer
import threading
import argparse
import time
import os

LatestPictureFilename = ""

def GetTimeStamp():
    ts = str(datetime.now())
    return ts.replace(' ', '-')


def ReadPictureSettings(args):
    global LatestPictureFilename
    LatestPictureFilename = GetTimeStamp() + ".jpg"
    try:
        with open(GetPictureSettings(args), 'r') as f:
            cmd = f.readline().strip()
            cmd += " " + GetPictureStorageDirectory(args) + "/" + LatestPictureFilename
            return cmd.split(' ')
    except Exception as e:
        print("Picture configuration file not found: " + e.__str__())
        return None

def Sync():
    call("sync")

def CopyAsLatestPicture(args):
    global LatestPictureFilename
    cmd = "cp " + GetPictureStorageDirectory(args) + "/" + LatestPictureFilename + " " + GetPictureStorageDirectory(args) + "/latest.jpg"
    return cmd.split(' ')


def TakeSnapShot(args):
    frequencySeconds = GetPictureFrequency(args)
    if (frequencySeconds == 0):
        return
    while True:
        call(ReadPictureSettings(args))
        Sync()
        call(CopyAsLatestPicture(args))
        if (GetServerPortNumber(args) == 0):
            break
        else:
            time.sleep(frequencySeconds)


def GetServerPortNumber(args):
    return int(args['port'][0])


def GetPictureFrequency(args):
    return int(args['freq'][0])


def GetPictureStorageDirectory(args):
    return args['dir'][0]


def GetPictureSettings(args):
    return args['conf'][0]


def OnCommand(args):
    os.chdir(GetPictureStorageDirectory(args))
    portNumber = GetServerPortNumber(args)
    if (portNumber > 0):
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        Httpd = SocketServer.TCPServer(("0.0.0.0", portNumber), Handler)
        t = threading.Thread(target=TakeSnapShot, args=(args,))
        print("SimpleHTTPServer listening on port " + str(portNumber) )
        t.start()
        Httpd.serve_forever()
    else:
        TakeSnapShot(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='snapshot.py', description="Raspberry Pi Image Server", usage='%(prog)s [options] [parameter]')
    group = parser.add_argument_group('server')
    group.add_argument('--port', nargs=1, type=int, help='HTTP listener port number. 0 = exit after taking a single shot')
    group = parser.add_argument_group('picture')
    group.add_argument('--freq', nargs=1, type=int, help='Picture taking frequency in seconds. 0 = take no pictures, HTTP server only')
    group.add_argument('--dir', nargs=1, type=str, help='Picture storage directory')
    group.add_argument('--conf', nargs=1, type=str, help='Picture configuration file path')
    
    args = vars(parser.parse_args())
    if 'help' in args:
        parser.parse_args("--help")
        exit()
        
    OnCommand(args)

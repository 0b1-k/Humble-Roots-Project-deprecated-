#!/usr/bin/env python
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
import json
from mqtt import MQTT
from time import sleep
from os import stat      
    
class Config(object):
    def __init__(self):
        self.data = None
        self.filename = None
        self._lastStat = None
        self._newData = None

    def Load(self, jsonCfgFile='./config/bootstrap.json'):
        self.data = None
        self.filename = jsonCfgFile
        self._lastStat = self.GetStats()
        with open(jsonCfgFile) as cfgFile:
            self.data = json.load(cfgFile)
        return self.data

    def GetRawContent(self):
        with open(self.filename) as cfgFile:
            return cfgFile.read()

    def OnConfigUpdate(self, client, userdata, msg):
        try:
            self._newData = json.loads(msg.payload)
        except:
            self._newData = None

    def IsChanged(self):
        changed = False
        _stat = self.GetStats()
        if _stat.st_mtime > self._lastStat.st_mtime or self._newData is not None:
            changed = True
            self._lastStat = _stat
        return changed

    def CommitChanges(self):
        if self._newData is not None:
            self.data = self._newData
            self._newData = None
            return self.data
            
    def GetStats(self):
        return stat(self.filename)

    def SyncUpdate(self):
        while not self.IsChanged():
            sleep(.1)
        return self.CommitChanges()

    def Idle(self, callback=None):
        exitFlag = False
        try:
            while not self.IsChanged() and not exitFlag:
                if callback is not None:
                    exitFlag = callback()
                else:
                    sleep(.1)
        except KeyboardInterrupt as e:
            print("kbd int. in " + __file__)
            exitFlag = True
        return exitFlag

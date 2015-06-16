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
import time
import sys
import json
import traceback
from config import Config
from mqtt import MQTT
from influxdb import InfluxDBClient
from utils import UrlDecode

class InfluxDBWriter(object):
    def __init__(self, config):
        self.config = config
        self.client = None
        self.sequence = 0
        
    def Connect(self):
        self.client = InfluxDBClient(
            self.config['influxDB']['host'],
            self.config['influxDB']['port'],
            self.config['influxDB']['user'],
            self.config['influxDB']['pswd'],
            self.config['influxDB']['db'])
    
    def Disconnect(self):
        self.client = None
        
    def Write(self, seriesName, points, columns, epoch, sequence=None):
        if(sequence is None):
            self.sequence += 1
            sequence = self.sequence
            
        jsonBody = [{
            "points": [[epoch, sequence],],
            "name": seriesName,
            "columns": ["time", "sequence_number"]
        }]
        
        jsonBody[0]["points"][0] += points
        jsonBody[0]["columns"] += columns

        self.client.write_points(jsonBody)
        #print(str(jsonBody))


class SensorDataParser(object):
    def __init__(self, dbWriter=None, config=None):
        self.dbWriter = dbWriter
        self.excludeKeys = dict()
        self.excludeKeys['node'] = None
        self.excludeKeys['ts'] = None
        self.excludeKeys['t'] = None
        self.acceptType = config['sensorDataParser']['accept']
        self.nodeMap = config['node']
     
    def Callback(self, client, userdata, msg):
        try:
            d = UrlDecode(msg.payload)
        except ValueError as e:
            print traceback.format_exc()
            return
        try:
            nodeType = d["t"][0]
            if nodeType not in self.acceptType:
                return
        except KeyError as e:
            return

        if self.dbWriter != None:
            pc = self._BuildPointsColumns(d)
            self.dbWriter.Write(
                self._BuildSeriesName(d),
                pc['points'],
                pc['columns'],
                self._GetEpoch(d))            
    
    def _BuildPointsColumns(self, data):
        d = dict()
        d['points'] = []
        d['columns'] = []
        for key in data:
            if key not in self.excludeKeys:
                d['columns'].append(key)
                value = None
                try:
                    value = int(data[key][0])
                except ValueError:
                    value = float(data[key][0])
                d['points'].append(value)
        return d

    def _BuildSeriesName(self, data):
        key = data['node'][0]
        if key in self.nodeMap:
            return self.nodeMap[key]
        else:
            return "node.{0}".format(key)
    
    def _GetSensorType(self, data):
        return data['t'][0]

    def _GetEpoch(self, data):
        return long(data['ts'][0], 10)

def OnIdle():
    time.sleep(1)
    return False

def Run():
    config = Config()
    cfgData = config.Load()

    print("MQTT started.")
    
    mq = MQTT(cfgData['mqtt']['rootPrefix'])
    mq.Start(cfgData['mqtt']['host'], int(cfgData['mqtt']['port']), int(cfgData['mqtt']['keepalive']))
    
    mq.Subscribe("config", config.OnConfigUpdate)
    cfgData = config.SyncUpdate()
    print("Config sync'ed.")
    
    dbw = InfluxDBWriter(cfgData)
    dbw.Connect()
    print("DB connected.")
    
    sdp = SensorDataParser(dbw, cfgData)
    mq.Subscribe(cfgData['serial']['pubPrefix'], sdp.Callback)
    print("Listening for sensor data.")
    
    exitFlag = config.Idle(OnIdle)
    print("Stopping...")
    
    mq.UnSubscribe(cfgData['serial']['pubPrefix'])
    mq.UnSubscribe("config")
    
    mq.Stop()
    dbw.Disconnect()
    
    return exitFlag

if __name__ == '__main__':
    exitCode = False
    while exitCode == False:
        print("Started: {0}".format(__file__))
        exitCode = Run()
    print("Stopped: {0}".format(__file__))

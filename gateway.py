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
from config import Config
from serialadapter import SerialAdapter
from mqtt import MQTT
from utils import GetSecondsSinceEpoch
import time

class Gateway(object):
    def __init__(self, config, pubSub):
        self.config = config
        self.pubSub = pubSub
        self.sa = SerialAdapter()

    def Start(self):
        self.sa.Start(
            self.config['serial']['port'],
            self.config['serial']['baudrate'],
            self.SerialRxCallback)
        self.pubSub.Subscribe(self.config['serial']['subPrefix'], self.SerialTxCallback)
    
    def Stop(self):
        self.pubSub.UnSubscribe(self.config['serial']['subPrefix'])
        self.sa.Stop()
        self.pubSub.Stop()
        
    def SerialRxCallback(self, data):
        self.pubSub.Publish(self.config['serial']['pubPrefix'], "{0}&ts={1}".format(data, GetSecondsSinceEpoch()))

    def SerialTxCallback(self, client, userdata, message):
        self.sa.Write("{0}\r\n".format(message.payload))
            
    def IsStopEventSet(self):
        return self.sa.stopEvent.isSet()

def Run():
    config = Config()
    cfgData = config.Load()

    print("MQTT started.")
    
    mq = MQTT(cfgData['mqtt']['rootPrefix'])
    mq.Start(cfgData['mqtt']['host'], int(cfgData['mqtt']['port']), int(cfgData['mqtt']['keepalive']))
    
    mq.Subscribe("config", config.OnConfigUpdate)
    cfgData = config.SyncUpdate()
    print("Config sync'ed.")
    
    gw = Gateway(cfgData, mq)
    gw.Start()
    
    print("Gateway started.")
    
    exitFlag = False
    try:
        while not gw.IsStopEventSet() and not config.IsChanged() and not exitFlag:
            time.sleep(.1)
    except KeyboardInterrupt as e:
        print("kbd int. in " + __file__)
        exitFlag = True
        
    print("Gateway stopping...")
    
    mq.UnSubscribe("config")
    
    gw.Stop()
    mq.Stop
    
    return exitFlag


if __name__ == '__main__':
    exitCode = False
    while exitCode == False:
        print("Started: {0}".format(__file__))
        exitCode = Run()
    print("Stopped: {0}".format(__file__))

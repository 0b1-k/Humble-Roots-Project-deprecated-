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
import traceback
from pb import PushBullet, HOST
from config import Config
from mqtt import MQTT
from utils import UrlDecode, GetSecondsSinceEpoch
from threading import Event
from string import lower, find

class Notifier(object):
    def __init__(self, cfgData):
        self.cfgData = cfgData
        self.lastModified = None
        self.notifier = None
        self.pubSub = None
        self.devices = dict()
        self.devices[self.cfgData["PushBullet"]["appDevice"]] = None
        self.devices[self.cfgData["PushBullet"]["alertDevice"]] = None
        self.user = None
        self.stopEvent = Event()
        self.stopEventCallbackCount = 0
        self.notifyHandlers = self.cfgData["PushBullet"]["accept"]
        self.notifyHandlers["note"] = self.PushNote
        self.notifyHandlers["alert"] = self.PushAlert
        
    def Start(self, mq):
        self.pubSub = mq
        self.notifier = PushBullet(self.cfgData["PushBullet"]["token"])
        self.user = self.notifier.getUser()
        deviceList = self.notifier.getDevices()
        for nickname in self.devices:
            identifier = self.IdentifyDevice(nickname, deviceList)
            if identifier is not None:
                self.devices[nickname] = identifier
            else:
                newDeviceData = self.notifier.addDevice(nickname)
                self.devices[nickname] = newDeviceData["iden"]
        self.lastModified = self.GetLastModified()
        self.notifier.realtime(self.CallbackInbound, self.stopEvent)
        
    def IdentifyDevice(self, nickname, deviceList):
        for device in deviceList:
            if "nickname" in device and device["nickname"] == nickname:
                return device["iden"]
        return None
        
    def GetLastModified(self):
        pushes = self.notifier.getPushHistory()
        return float(pushes[0]["modified"]) - 1.0

    def Stop(self):
        self.stopEvent.set()
    
    def CallbackInbound(self, data):
        if isinstance(data, dict) and "type" in data and "subtype" in data:
            pushes = self.notifier.getPushHistory(modified_after=self.lastModified)
            for push in pushes:
                if "type" in push and "active" in push and "dismissed" in push and "modified" in push:
                    if push["type"] == "note" and push["active"] == True and push["dismissed"] == False and push["modified"] > self.lastModified:
                        self.lastModified = push["modified"]
                        self.ForwardMessage(push["title"], push["body"])

    def _GetSignature(self):
        return "[{0}]".format(self.cfgData["PushBullet"]["appDevice"])
    
    def ForwardMessage(self, title, body):
        if find(title, self._GetSignature()) != -1:
            return
        try:
            forward = False
            d = UrlDecode(lower(body))
            if "node" in d and "cmd" in d and "r" in d and "s" in d:
                forward = True
            elif "get" in d and d["get"][0] == "report":
                forward = True
            if forward:
                self.pubSub.Publish(self.cfgData["control"]["command"]["subPrefix"], body)
                print("Title: {0}, Body: {1}".format(title, body))
            else:
                print("Invalid message: {0}".format(body))
        except ValueError as e:
            print("Malformed message: {0}".format(body))

    def CallbackNotify(self, client, userdata, msg):
        try:
            d = UrlDecode(msg.payload)
        except ValueError as e:
            print("Invalid message: {0}".format(msg.payload))
            return
        try:
            handlerType = d["type"][0]
            func = self.notifyHandlers[handlerType]
            func(d)
        except KeyError as e:
            print("Invalid notification type: {0}".format(msg.payload))
            return

    def PushAlert(self, data):
        body = data["body"][0]
        try:
            self.notifier.pushSMS(
                self.user["iden"],
                self.devices[self.cfgData["PushBullet"]["alertDevice"]],
                self.cfgData["PushBullet"]["alertNumber"],
                body)
        except Exception as e:
            print("PushAlert failed: {0}".format(str(e)))
    
    def PushNote(self, data):
        try:
            self.notifier.pushNote(
                self.devices[self.cfgData["PushBullet"]["appDevice"]],
                "{0} {1}".format(self._GetSignature(), data["title"][0]),
                data["body"][0])
        except Exception as e:
            print("PushNote failed: {0}".format(str(e)))
        
    def CallbackStopEvent(self, client, userdata, msg):
        self.stopEventCallbackCount += 1
        if self.stopEventCallbackCount > 1:
            self.Stop()
    
def Run():
    config = Config()
    cfgData = config.Load()
    
    mq = MQTT(cfgData['mqtt']['rootPrefix'])
    mq.Start(cfgData['mqtt']['host'], int(cfgData['mqtt']['port']), int(cfgData['mqtt']['keepalive']))
    print("MQTT started.")
    
    mq.Subscribe("config", config.OnConfigUpdate)
    cfgData = config.SyncUpdate()

    print("Config sync'ed.")
    print("Notifier started...")
    
    n = Notifier(cfgData)

    mq.UnSubscribe("config")
    mq.Subscribe("config", n.CallbackStopEvent)
    mq.Subscribe(cfgData["PushBullet"]["subPrefix"], n.CallbackNotify)
    
    try:
        n.Start(mq)
    except Exception as e:
        print(str(e))
    
    print("Stopping...")
    
    mq.UnSubscribe("config")
    mq.Stop()
    
    return False

if __name__ == '__main__':
    exitCode = False
    while exitCode == False:
        print("Started: {0}".format(__file__))
        exitCode = Run()
    print("Stopped: {0}".format(__file__))


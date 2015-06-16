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
import datetime
import sys
import json
import traceback
import gc
import hashlib
from time import sleep, strftime
from threading import Lock
from config import Config
from mqtt import MQTT
from utils import UrlDecode, UrlEncode, GetSecondsSinceEpoch
from send import Command
from string import lower
from report import Report

class Controller():
    def __init__(self, cfgData, pubSub):
        self.cfgData = cfgData
        self.pubSub = pubSub
        self.acceptType = cfgData['sensorDataParser']['accept']
        self.nodeMap = cfgData['node']
        self.controlRules = cfgData["control"]
        self.cmd = Command(self.cfgData)
        self.activeAlerts = dict()
        self.tickFreqSec = float(cfgData['control']['tick']["freqSec"])
        self.nodeTimeoutTrackerLock = Lock()
        self.nodeTimeoutSec = self.controlRules["nodeTimeout"]["freqSec"]
        self.nodeTimeoutTracker = self._InitNodeTimeoutTracker(self.nodeMap, self.nodeTimeoutSec)
        self.timeTrack = self.tickFreqSec
        self.timeTrackWaitSec = 0.01
        self.report = Report(cfgData)
        
    def Start(self):      
        self.cmd.Start()
        self.pubSub.Subscribe(self.cfgData['serial']['pubPrefix'], self.CallbackSensor)
        self.pubSub.Subscribe(self.cfgData['control']['tick']["subPrefix"], self.CallbackTime)
        self.pubSub.Subscribe(self.cfgData["control"]["command"]["subPrefix"], self.CallbackShell)
        
    def TrackTime(self):
        sleep(self.timeTrackWaitSec)
        self.timeTrack -= self.timeTrackWaitSec
        if self.timeTrack <= 0:
            self.timeTrack = self.tickFreqSec
            self.pubSub.Publish(
                self.cfgData['control']['tick']["subPrefix"],
                "ts={0}".format(GetSecondsSinceEpoch()))

    def Stop(self):
        self.pubSub.UnSubscribe(self.cfgData['serial']['pubPrefix'])
        self.pubSub.UnSubscribe(self.cfgData['control']['tick']["subPrefix"])
        self.pubSub.UnSubscribe(self.cfgData["control"]["command"]["subPrefix"])
        self.cmd.Stop()
    
    def _UrlDecode(self, url):
        d = None
        try:
            d = UrlDecode(url)
        except ValueError as e:
            print traceback.format_exc()
        return d
        
    def CallbackSensor(self, client, userdata, msg):
        d = self._UrlDecode(msg.payload)
        if d is None:
            return
        try:
            nodeType = d["t"][0]
            if nodeType not in self.acceptType:
                return
        except KeyError as e:
            return
        
        if "node" in d:
            self._ResetNodeTimeout(d["node"][0])
        
        if nodeType in self.controlRules:
            ruleList = self.controlRules[nodeType]
            for rule in ruleList:
                rc = self._EvalRule(rule, d)
        
        ruleList = self.controlRules["signal"]
        for rule in ruleList:
            rc = self._EvalRule(rule, d)
            
        self.report.Update(d)
    
    def CallbackTime(self, client, userdata, msg):
        d = self._UrlDecode(msg.payload)
        if d is None:
            return
        if "ts" in d:
            timeRules = self.controlRules["timers"]
            if timeRules is not None:
                for rule in timeRules:
                    rc = self._EvalRule(rule, d)
            self._TrackNodeTimeout()
        
    def _InitNodeTimeoutTracker(self, nodeMap, freqSec):
        nt = dict()
        for nodeID in nodeMap:
            nt[nodeID] = freqSec
        return nt

    def _TrackNodeTimeout(self):
        self.nodeTimeoutTrackerLock.acquire()
        for nodeID in self.nodeTimeoutTracker:
            if self.nodeTimeoutTracker[nodeID] > 0:
                self.nodeTimeoutTracker[nodeID] -= self.tickFreqSec
            if self.nodeTimeoutTracker[nodeID] <= 0:
                self.SendAlert(self.nodeTimeoutSec, self._BuildNodeTimeoutRule(), nodeID)
        self.nodeTimeoutTrackerLock.release()
    
    def _ResetNodeTimeout(self, nodeID):
        self.nodeTimeoutTrackerLock.acquire()
        self.nodeTimeoutTracker[nodeID] = self.nodeTimeoutSec
        self.ClearAlert(self.nodeTimeoutSec, self._BuildNodeTimeoutRule(), nodeID)
        self.nodeTimeoutTrackerLock.release()

    def CallbackShell(self, client, userdata, msg):
        if self.cfgData["control"]["command"]["enabled"] == 1:
            print("-----------------------\r\nForwarded command: {0}".format(msg.payload))
            d = UrlDecode(lower(msg.payload))
            if "node" in d and "cmd" in d and "r" in d and "s" in d:
                self.cmd.Shell(msg.payload)
            elif "get" in d and d["get"][0] == "report" and self.cfgData["control"]["command"]["report"]["enabled"] == 1:
                self.SendNote(
                    self.report.GetTitle(),
                    self.report.GetBody())
        else:
            print("Remote interface disabled.")
                        
    def _EvalRule(self, rule, data):
        if rule["enabled"] == 1:
            print("-----------------------")
            if "node" in data:
                nodeID = data["node"][0]
                if "node" in rule and self.nodeMap[nodeID] != rule["node"]:
                        return
                else:
                    print("node:{0}".format(self.nodeMap[nodeID]))
            else:
                nodeID = None
            value = float(data[rule["value"]][0])
            print("value={0}".format(value))
            if "alert" in rule and nodeID is not None:
                if self._EvalCondition(value, rule["alert"], data) == True:
                    self.SendAlert(value, rule, nodeID)
                else:
                    self.ClearAlert(value, rule, nodeID)
            preReqs = list()
            if "time" in rule:
                preReqs.append(self._EvalCondition(value, rule["time"], data))
            if False in preReqs:
                return self._SendCommand(rule, "off")
            if "on" in rule and self._EvalCondition(value, rule["on"], data) == True:
                return self._SendCommand(rule, "on")
            elif "off" in rule and self._EvalCondition(value, rule["off"], data) == True:
                return self._SendCommand(rule, "off")

    def SendAlert(self, value, rule, nodeID):
        ruleHash = self.GetRuleHash(rule, nodeID)
        now = GetSecondsSinceEpoch()
        if ruleHash not in self.activeAlerts:
            self.activeAlerts[ruleHash] = {"created": now, "modified": now}
            self.pubSub.Publish(
                self.cfgData["PushBullet"]["subPrefix"],
                self.ComposeAlert(value, rule, nodeID))
        else:
            self.activeAlerts[ruleHash]["modified"] = now
    
    def SendNote(self, title, msg):
        self.pubSub.Publish(
            self.cfgData["PushBullet"]["subPrefix"],
            self.ComposeNote(title, msg))
        
    def _BuildNodeTimeoutRule(self):
        rule = {
            "alert": {
                "op": "=",
                "setpoint": self.controlRules["nodeTimeout"]["freqSec"],
                "title": self.controlRules["nodeTimeout"]["title"]
                }
            }
        return rule
    
    def ComposeAlert(self, value, rule, nodeID, clear=False):
        if nodeID is not None:
            nodeName = self.nodeMap[nodeID]
        else:
            nodeName = "?" 
        if clear:
            clearMark = "|CLEARED|"
        else:
            clearMark = "|"
        data = {
            "type": "alert",
            "body": "[{0}] {1} {2} {3} {4} {5} @ {6}".format(
                nodeName,
                rule["alert"]["title"],
                clearMark,
                value,
                rule["alert"]["op"],
                rule["alert"]["setpoint"],
                strftime('%X %x %Z'))
            }
        return UrlEncode(data)
    
    def ComposeNote(self, title, msg):
        data = {
            "type": "note",
            "title": title,
            "body": "{0} @ {1}".format(msg, strftime('%X %x %Z'))
            }
        return UrlEncode(data)

    def ClearAlert(self, value, rule, nodeID):
        ruleHash = self.GetRuleHash(rule, nodeID)
        if ruleHash in self.activeAlerts:
            self.pubSub.Publish(
                self.cfgData["PushBullet"]["subPrefix"],
                self.ComposeAlert(value, rule, nodeID, clear=True))
            self.activeAlerts.pop(ruleHash)
    
    def GetRuleHash(self, rule, nodeID):
        h = hashlib.md5()
        h.update(str(rule))
        h.update(str(nodeID))
        return h.hexdigest()
    
    def _SendCommand(self, rule, onOff):
        print(str(rule[onOff]["cmd"]))
        self.cmd.Shell(rule[onOff]["cmd"])
        
    def _EvalCondition(self, value, condition, data):
        print(str(condition))
        if "from" in condition and "to" in condition:
            ftInt = condition["from"].split(':')
            ttInt = condition["to"].split(':')
            fromTime = datetime.time(int(ftInt[0]), int(ftInt[1]))
            toTime = datetime.time(int(ttInt[0]), int(ttInt[1]))
            return self._IsTimeWithinRange(datetime.datetime.now().time(), fromTime, toTime)
        elif "op" in condition and "setpoint" in condition:
            setPoint = float(condition["setpoint"])
            if condition["op"] == "==":
                if value == setPoint:
                    return True
            elif condition["op"] == ">=":
                if value >= setPoint:
                    return True
            elif condition["op"] == "<=":
                if value <= setPoint:
                    return True
            elif condition["op"] == ">":
                if value > setPoint:
                    return True
            elif condition["op"] == "<":
                if value < setPoint:
                    return True
            elif condition["op"] == "!=":
                if value != setPoint:
                    return True
            else:
                raise "Invalid op"
        elif "op" not in condition and "cmd" in condition:
            return True
        else:
            return False
        
    def _IsTimeWithinRange(self, timeNow, fromTime, toTime):
        if fromTime > toTime:
            if timeNow > fromTime or timeNow < toTime:
                return True
        elif fromTime < toTime:
            if timeNow > fromTime and timeNow < toTime:
                return True
        elif fromTime == toTime:
            if timeNow == fromTime:
                return True
        return False

    
def Run():
    config = Config()
    cfgData = config.Load('./config/config.json')
    print("config loaded.")
    
    mq = MQTT(cfgData['mqtt']['rootPrefix'])
    mq.Start(cfgData['mqtt']['host'], int(cfgData['mqtt']['port']), int(cfgData['mqtt']['keepalive']))
    print("MQTT started.")
    
    mq.Publish(cfgData["control"]["config"]["subPrefix"], config.GetRawContent(), retain=True)
    print("Config published.")
    
    ctl = Controller(cfgData, mq)
    ctl.Start()
    print("Controller started.")
    
    exitFlag = False
    try:
        while not config.IsChanged() and not exitFlag:
            ctl.TrackTime()
    except KeyboardInterrupt as e:
        print("kbd int. in " + __file__)
        exitFlag = True

    print("Controller stopping...")
    ctl.Stop()
    print("Controller stopped.")
    
    mq.Stop()
    print("MQTT stopped.")
    
    gc.collect()
    print("GC collection complete.")
    
    return exitFlag

if __name__ == '__main__':
    exitCode = False
    while exitCode == False:
        print("Started: {0}".format(__file__))
        exitCode = Run()
    print("Stopped: {0}".format(__file__))

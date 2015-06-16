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
class Report(object):
    def __init__(self, cfgData):
        self.cfgData = cfgData
        self.nodeMap = cfgData["node"]

    def Update(self, data):
        if "node" in data:
            nodeName = self.nodeMap[data["node"][0]]
            reportRuleList = self.cfgData["report"]["node"][nodeName]
            for rule in reportRuleList:
                if "state" in rule and rule["state"] in data:
                    if "states" not in rule:
                        rule["states"] = dict()
                    rule["states"][self._GetValue(rule, data)] = self._GetState(rule, data)
                else:
                    rule["valueData"] = self._GetValue(rule, data)

    def _GetValue(self, rule, data):
        valueData = data[rule["value"]][0]
        if rule["value"] in self.cfgData:
            return self.cfgData[rule["value"]][valueData]
        else:
            return float(valueData)

    def _GetState(self, rule, data):
        stateData = data[rule["state"]][0]
        if rule["state"] in self.cfgData:
            return self.cfgData[rule["state"]][stateData]
        else:
            return stateData

    def GetBody(self):
        r = list()
        nodes = self.cfgData["report"]["node"]
        for nodeName in nodes:
            r.append("Node: {0}\r\n".format(nodeName))
            reportRuleList = self.cfgData["report"]["node"][nodeName]
            for rule in reportRuleList:
                if "states" not in rule and "valueData" in rule:
                    r.append("{0}: {1} {2}\r\n".format(rule["label"], rule["valueData"], rule["unit"]))
                elif "states" in rule:
                    for k, v in rule["states"].iteritems():
                        r.append("{0}: {1}\r\n".format(k, v))
            r.append("{0}\r\n".format(self.cfgData["report"]["divider"]))
        return "".join(r)

    def GetTitle(self):
        return self.cfgData["report"]["title"]

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
import paho.mqtt.client as mqtt
import time
from utils import GetTimeStamp, UrlEncode, UrlDecode

class MQTT(object):
    def __init__(self, publisherPrefix="foo"):
        self._mqtt = mqtt.Client()
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_disconnect = self._on_disconnect
        self._mqtt.on_message = self._on_message
        self._mqtt.on_publish = self._on_publish
        self._mqtt.on_subscribe = self._on_subscribe
        self._mqtt.on_unsubscribe = self._on_unsubscribe
        self._mqtt.on_log = self._on_log
        self.publisherPrefix = publisherPrefix

    def __exit__(self):
        self.Stop()
        
    def Start(self, host, port, keepalive):
        self._mqtt.connect(host, port, keepalive)
        self._mqtt.loop_start()
        
    def Stop(self):
        self._mqtt.disconnect()
        self._mqtt.loop_stop()

    def Publish(self, topic, payload, retain=False, UrlEncode=False):
        if UrlEncode == True:
            p = UrlEncode(payload)
        else:
            p = payload
        topic=self.GetCanonicalTopic(topic)
        self._mqtt.publish(topic, payload=p, qos=0, retain=retain)
    
    def Subscribe(self, topic, callback):
        t = self.GetCanonicalTopic(topic)
        self._mqtt.message_callback_add(t, callback)
        self._mqtt.subscribe(t)

    def UnSubscribe(self, topic):
        t = self.GetCanonicalTopic(topic)
        self._mqtt.message_callback_remove(t)
        self._mqtt.unsubscribe(t)
        
    def _on_connect(self, client, userdata, flags, rc):
        print(mqtt.connack_string(rc))
    
    def _on_disconnect(self, client, userdata, rc):
        print(mqtt.error_string(rc))
    
    def _on_message(self, client, userdata, message):
        pass
    
    def _on_publish(self, client, userdata, mid):
        pass
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass
    
    def _on_unsubscribe(self, client, userdata, mid):
        pass
    
    def _on_log(self, client, userdata, level, buf): 
        if (level == mqtt.MQTT_LOG_INFO):
            pass
        elif (level == mqtt.MQTT_LOG_NOTICE):
            pass
        elif (level == mqtt.MQTT_LOG_WARNING):
            pass
        elif (level == mqtt.MQTT_LOG_ERR):
            pass
        elif (level == mqtt.MQTT_LOG_DEBUG):
            pass

    def GetCanonicalTopic(self, topic):
        return "{0}/{1}".format(self.publisherPrefix, topic)
    
    def GetTime(self):
        return time.time()

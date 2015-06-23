#!/usr/bin/python

# Copyright (c) 2010-2013 Roger Light <roger@atchoo.org>
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Distribution License v1.0
# which accompanies this distribution. 
#
# The Eclipse Distribution License is available at 
#   http://www.eclipse.org/org/documents/edl-v10.php.
#
# Contributors:
#	Roger Light - initial implementation
#	Fabien Royer - prints "Humble Roots Project" messages to the console.
#
# Copyright (c) 2010,2011 Roger Light <roger@atchoo.org>
# All rights reserved.

# This shows a simple example of an MQTT subscriber.
import paho.mqtt.client as mqtt

def on_connect(mqttc, obj, flags, rc):
    print("Connected ({0})".format(rc))

def on_message(mqttc, obj, msg):
    print("{0}".format(msg.payload))

mqttc = mqtt.Client()

mqttc.on_message = on_message
mqttc.on_connect = on_connect

mqttc.connect("localhost", 1883, 60)
mqttc.subscribe("hrs/#", 0)

mqttc.loop_forever()


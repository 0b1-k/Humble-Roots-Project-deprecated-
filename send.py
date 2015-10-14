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
import sys
import random
import logging
import logging.config
from config import Config
from mqtt import MQTT
from utils import UrlDecode, UrlEncode
from time import sleep
from hashids import Hashids
from os import urandom
from threading import Lock, Event, Thread

logging.config.fileConfig('./config/logger.ini')
logger = logging.getLogger('Roots')

class Command(object):
    STATUS_TIMEOUT = -1
    STATUS_PENDING = 0
    STATUS_ACK = 1
    STATUS_NACK = 2
    STATUS_TIMEOUT_STR = "timeout"
    STATUS_PENDING_STR = ""
    STATUS_ACK_STR = "ack"
    STATUS_NACK_STR = "nack"
    TIMER_INTERVAL_SEC = .1
    TIMER_WAIT_TIME_SEC = .01
    MAX_SEND_COMMAND_TIMEOUT_SEC = .5
    MAX_SEND_COMMAND_RETRIES = 2
    
    def __init__(self, cfgData):
        self.cfgData = cfgData
        self.mq = MQTT(self.cfgData['mqtt']['rootPrefix'])
        self.hash = Hashids(salt=urandom(16), min_length=5)
        self.count = random.randint(0, 999)
        self.tokens = dict()
        self.tokensLock = Lock()
        self.timerThreadExitEvent = Event()
        
        self.stateToStateStr = dict()
        self.stateToStateStr[self.STATUS_TIMEOUT] = self.STATUS_TIMEOUT_STR
        self.stateToStateStr[self.STATUS_PENDING] = self.STATUS_PENDING_STR
        self.stateToStateStr[self.STATUS_ACK] = self.STATUS_ACK_STR
        self.stateToStateStr[self.STATUS_NACK] = self.STATUS_NACK_STR
        
        self.stateStrToState= dict()
        self.stateStrToState[self.STATUS_TIMEOUT_STR] = self.STATUS_TIMEOUT
        self.stateStrToState[self.STATUS_PENDING_STR] = self.STATUS_PENDING
        self.stateStrToState[self.STATUS_ACK_STR] = self.STATUS_ACK
        self.stateStrToState[self.STATUS_NACK_STR] = self.STATUS_NACK

    def Start(self):
        self.timerThread = Thread(target=self._ElapseTime)
        self.timerThread.start()
        self.mq.Start(
            self.cfgData['mqtt']['host'],
            int(self.cfgData['mqtt']['port']),
            int(self.cfgData['mqtt']['keepalive']))
        self.mq.Subscribe(self.cfgData['serial']['pubPrefix'], self._SerialRxCallback)

    def Shell(self, cmd=None):
        if cmd is None:
            while True:
                try:
                    cmd = raw_input(">")
                except KeyboardInterrupt as e:
                    break
                if cmd.startswith("exit"):
                    break
                self._SendCommand(cmd)
        else:
            self._SendCommand(cmd)
        
    def Stop(self):
        self.mq.UnSubscribe(self.cfgData['serial']['pubPrefix'])
        self.mq.Stop()
        self.timerThreadExitEvent.set()
        self.timerThread.join()

    def _AppendToken(self, cmd, token):
        return "{0}&tok={1}".format(cmd, token)
    
    def _GetToken(self):
        self.tokensLock.acquire()
        self.count += 1
        token = self.hash.encode(self.count)
        self.tokens[token] = [self.MAX_SEND_COMMAND_TIMEOUT_SEC, self.STATUS_PENDING_STR]
        self.tokensLock.release()
        return token

    def _DeleteToken(self, token):
        self.tokensLock.acquire()
        del self.tokens[token]
        self.tokensLock.release()
        
    def _SendCommand(self, cmd):
        retries = self.MAX_SEND_COMMAND_RETRIES
        result = self.STATUS_PENDING
        while retries > 0 and not self.timerThreadExitEvent.isSet() and result != self.STATUS_ACK:
            retries -= 1
            result = self.STATUS_PENDING
            token = self._GetToken()
            try:
                resolvedCmd = self._Resolve(cmd)
                resolvedCmd = self._AppendToken(resolvedCmd, token)
                self.mq.Publish(self.cfgData["serial"]["subPrefix"], resolvedCmd)
                logger.info("Pending")
                while result == self.STATUS_PENDING and not self.timerThreadExitEvent.isSet():
                    sleep(self.TIMER_WAIT_TIME_SEC)
                    result = self._GetCommandStatus(token)
                logger.info(self.stateToStateStr[result])
            except:
                logger.error("Bad command: {0}".format(cmd))
                retries = 0
            finally:
                self._DeleteToken(token)
        return result

    def _ElapseTime(self):
        while not self.timerThreadExitEvent.isSet():
            self.tokensLock.acquire()
            for token in self.tokens:
                state = self.tokens[token]
                if state[0] >= -1.0:
                    state[0] -= self.TIMER_WAIT_TIME_SEC
                    self.tokens[token] = state
            self.tokensLock.release()
            sleep(self.TIMER_WAIT_TIME_SEC)

    def _GetCommandStatus(self, token):
        self.tokensLock.acquire()
        state = self.tokens[token]
        self.tokensLock.release()
        if state[0] < 0.0:
            return self.STATUS_TIMEOUT
        else:
            return self.stateStrToState[state[1]]

    def _Resolve(self, data):
        decoded = UrlDecode(data)
        for key in decoded:
            if key in self.cfgData:
                value = decoded[key][0]
                try:
                    int(value, 10)
                    continue
                except:
                    pass
                try:
                    subValue = self._GetKeyByValue(self.cfgData[key], value)
                    if subValue is None:
                        logger.error("Unresolved: key[{0}], value[{1}] in {2}".format(key, value, data))
                        raise
                    else:
                        decoded[key][0] = subValue
                except Exception as e:
                    raise e
        return UrlEncode(decoded)

    def _GetKeyByValue(self, dictMap, value):
        for k, v in dictMap.iteritems():
            if v == value:
                return k
        return None
    
    def _SerialRxCallback(self, client, userdata, message):
        if message.payload.find("&tok=") > -1 and message.payload.find("&tx=") > -1:
            decoded = UrlDecode(message.payload)
            token = decoded["tok"][0]
            txResult = decoded["tx"][0]
            self.tokensLock.acquire()
            try:
                state = self.tokens[token]
                state[1] = txResult
                self.tokens[token] = state
            except:
                pass
            self.tokensLock.release()

if __name__ == '__main__':
    config = Config()
    cfgData = config.Load('./config/config.json')
    cmd = Command(cfgData)
    cmd.Start()
    cmd.Shell()
    cmd.Stop()
    

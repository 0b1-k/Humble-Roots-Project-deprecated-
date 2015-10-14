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
import serial
import time
import threading
import traceback
from config import Config

class SerialAdapter(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.stopEvent = threading.Event()
    
    def Start(self, port, baudRate, callback=None, validDataKey="Listening"):
        self.validDataKey = validDataKey
        self.Callback = callback
        self.stopEvent.clear()
        self.comPort = serial.Serial(port, baudRate)
        self.comPort.timeout = 0.01
        self.start()
        
    def run(self):
        while True:
            try:
                valid = False
                inBytes = []
                while not self.stopEvent.isSet():
                    data = self.comPort.read()
                    if data != None:
                        if data == '\r':
                            continue
                        if data == '\n':
                            if valid == False:
                                chunk = "".join(inBytes)
                                if chunk.startswith(self.validDataKey) > -1:
                                    valid = True
                                inBytes = []
                                continue
                            else:
                                if self.Callback is not None:
                                    try:
                                        self.Callback("".join(inBytes))
                                    except Exception as e:
                                        print traceback.format_exc()
                                inBytes = []
                        else:
                            inBytes.append(data)
                    else:
                        time.sleep(0.01)
                break
            except Exception as e:
                self._OnException(e)
                break
        return

    def Write(self, data):
        self.comPort.write(data)
        self.comPort.flushOutput()
        
    def Stop(self):
        self.stopEvent.set()
        self.join()
        
    def _OnException(self, e):
        print("{0}", e.__str__())
        self.stopEvent.set()
        time.sleep(0.1)

def Callback(data):
    print data
    
if __name__ == '__main__':
    try:
        cfgData = Config().Load('./config/config.json')
        sa = SerialAdapter()
        sa.Start(cfgData['serial']['port'], cfgData['serial']['baudrate'], Callback)
        time.sleep(20)
        sa.Stop()
        print "Completed"
    except KeyboardInterrupt as e:
        sa.Stop()

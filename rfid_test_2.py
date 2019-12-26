'''
Rfid reader test
'''

import time
import serial


port = "/dev/ttyUSB0"
reader = serial.Serial('/dev/ttyUSB0',9600)
reader.flushInput()
reader.flushOutput()
while True:
    try:
        taginfo = reader.read()
        print("tag info:",taginfo)
        time.sleep(.5)
        # eader.serialPort.flushInput()
    except Exception as e:
        print("error reading tag:",e)
    reader.flushInput()
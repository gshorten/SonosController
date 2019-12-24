'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyUSB0")
while True:
    try:
        taginfo = reader.readTag()
        print("tag info:",taginfo)
        time.sleep(1)
        reader.serialPort.flushInput()
    except Exception as e:
        print("error reading tag:",e)
    reader.serialPort.flushInput()
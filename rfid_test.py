'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyUSB0")
while True:
    taginfo = reader.readTag()
    print("tag info:",taginfo)
    time.sleep(1)
    reader.serialPort.flushInput()

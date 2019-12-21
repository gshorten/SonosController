'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyS0")
while True:
    taginfo = reader.readTag()
    print("tag info:",taginfo)
    time.sleep(1)


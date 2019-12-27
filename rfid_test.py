'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyUSB0")
while True:
    response = input("0 to read tag")
    if response == '0':
        taginfo = reader.readTag()
        print("tag info:",taginfo)
        reader.serialPort.flushInput()

    # try:
    #
    #     time.sleep(.1)
    #
    # except Exception as e:
    #     print("error reading tag:",e)
    # reader.serialPort.flushInput()
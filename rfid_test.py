'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyUSB0")
while True:
    response = input("Enter to read tag")
    if response:
        try:
            for i in range (20):
                taginfo = reader.readTag()
                print("tag info:",taginfo)

        except Exception as e:
            print("error reading tag:",e)
        # reader.serialPort.flushInput()


    # try:
    #
    #     time.sleep(.1)
    #
    # except Exception as e:
    #     print("error reading tag:",e)
    # reader.serialPort.flushInput()
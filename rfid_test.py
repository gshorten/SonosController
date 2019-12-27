'''
Rfid reader test
'''

import time
import serial
import RFIDTagReader

reader = RFIDTagReader.TagReader("/dev/ttyUSB0")
while True:

    # taginfo = reader.readTag()
    # print ("tag: ",taginfo)
    # reader.serialPort.flushInput()

    response = input("Enter to read tag")
    if response:
        try:
            print("reading tag")
            for i in range (20):
                taginfo = reader.readTag()
                print("tag info:",taginfo)
                time.sleep(.1)

        except Exception as e:
            print("error reading tag:",e)
        reader.serialPort.flushInput()


    # try:
    #
    #     time.sleep(.1)
    #
    # except Exception as e:
    #     print("error reading tag:",e)
    # reader.serialPort.flushInput()
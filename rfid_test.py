'''
Rfid reader test
'''

import serial
serial = serial.Serial("/dev/ttyUSB0", baudrate=9600)
import time

code = ''
print('starting loop')
while True:
        data = serial.read()
        print("reading rfid: ",data)
        if data == '\r':
                print(code)
                code = ''
        else:
                code = code + data
        time.sleep(1)
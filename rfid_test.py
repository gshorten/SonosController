'''
Rfid reader test
'''

import serial
serial = serial.Serial("/dev/ttyUSB0", baudrate=9600)

code = ''

while True:
        data = serial.read()
        if data == '\r':
                print(code)
                code = ''
        else:
                code = code + data
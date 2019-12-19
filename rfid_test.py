'''
Rfid reader test
'''

import time
import serial

ser = serial.Serial(port='/dev/ttyUSB0', baudrate = 9600)
                    # parity=serial.PARITY_NONE,
                    # stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,timeout=1)
counter=0
print(ser)

while True:
    data = ser.read()
    print("Data:",data)
    time.sleep(1)


'''
Rfid reader test
'''



def main():
    with open('/dev/tty0', 'r') as tty:
        RFID_input = tty.readline()

        return(RFID_input)


#test
while True:
    rfid_code = main()
    print (rfid_code)
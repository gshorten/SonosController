#! /usr/bin/python3

#-*-coding: utf-8 -*-

import serial

class AHF_TagReader:

    """
    Class to read values from a Innovations RFID tag reader, such as ID-20LA
    """

    def __init__(self, serialPort, doChecksum = False, timeOutSecs = -1):

        """
        Makes a new AHF_TagReader object
        :param serialPort: serial port tag reader is attached to, /dev/ttyUSB0 or /dev/ttyAMA0 for instance
        :param doCheckSum: set to calculate the checksum on each tag read
        :param timeOutSecs:sets time out value. Use -1 for no time out, won't return until a tag has ben read
        """

        # initialize serial port
        self.serialPort = None

        try:
            if (timeOutSecs < 0):
                self.serialPort = serial.Serial(str (serialPort), baudrate=9600)
            else:
                self.serialPort = serial.Serial(str (serialPort), baudrate=9600, timeout=timeOutSecs)

        except IOError as anError:
            print ("Error initializing TagReader serial port.." + str (anError))
            raise anError
        if (self.serialPort.isOpen() == False):
            self.serialPort.open()

        self.serialPort.flushInput()
        # set boolean for doing checksum on each read
        self.doCheckSum = bool(doChecksum)

    def clearBuffer (self):
        """
        Clears the serial buffer for the serialport used by the tagReader
        """
        self.serialPort.flushInput()

    def readTag (self):
        """
        Reads a hexidecimal RFID tag from the serial port and returns the decimal equivalent
        RFID Tag is 16 characters: STX(02h) DATA (10 ASCII) CHECK SUM (2 ASCII) CR LF ETX(03h)

        :returns: decimal value of RFID tag, or 0 if no tag and non-blocking reading was specified
        :raises:IOError:if serialPort not read

        raises:ValueError:if either checksum or conversion from hex to decimal fails
        """

        rawTag = self.serialPort.readline() #consumes an entire line up to CR LF or times out and consumes nothing at all
        if rawTag.__len__() ==0: # the read timed out, so return 0
            return 0
        elif rawTag.__len__() < 15: #this should never happen
            self.serialPort.flushInput()
            raise IOError

        self.serialPort.read (1) # to clear the ETX that comes AFTER the CR LF
        serialTag = rawTag [1:11]

        try:
            decVal = int(serialTag, 16)
        except ValueError as anError:
            print ("TagReader Error converting tag to integer: " + str (serialTag) + ': ' + str (anError))
            self.serialPort.flushInput()
            raise ValueError

        else:
            if self.doCheckSum == True:
                serialCheckSum = rawTag [11:13] # pluck out the 2byte check sum
                if self.checkSum(serialTag, serialCheckSum)== True:
                    return decVal
                else:
                    print ("TagReader checksum error: " + str (serialTag) + ': ' + str (serialCheckSum))
                    self.serialPort.flushInput()
                    raise ValueError
            else:
                return decVal

    def checkSum(self, tag, checkSum):
        """
           Sequentially XOR-ing 2 byte chunks of the 10 byte tag value will give the 2-byte check sum
           :param tag: the 10 bytes of tag value
           :param checksum: the two bytes of checksum value
           :returns: True if check sum calculated correctly, else False
        """

        checkedVal = 0
        try:
            for i in range (0,5):
                checkedVal = checkedVal ^ int(tag [(2 * i) : (2 * (i + 1))], 16)
            if checkedVal == int(checkSum, 16):
                return True
            else:
                return False

        except Exception:
            return False

    def __del__(self):

        if self.serialPort is not None:
            self.serialPort.close()

if __name__ == '__main__':
    serialPort = '/dev/ttyUSB0'
    doCheckSum = True
    nReads =200
    try:
        tagReader = AHF_TagReader (serialPort, doCheckSum, timeOutSecs = 0.1)
    except Exception:
        print ('Tag reader not found, check port ' + serialPort)

    for i in range (0,nReads):
        print (tagReader.readTag ())
    print ('Read ' + str (nReads) + ' tags')
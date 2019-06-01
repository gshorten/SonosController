
import SonosUtils
import time
from Adafruit_CharLCD import Adafruit_CharLCDPlate

"""
Legacy Adafruit display module - no longer supported - use with raspberry pi zero.

The pizero does not seem to support Blinka, which is needed to work with curcuitpy, the new Adafruit 
    display modules for working with the i2c displays.  This works but Adafruit_CharLCD has to be installed manually,
    cannot use pip to install.
"""


class ExtendedLCD(Adafruit_CharLCDPlate, LCD):
    """"
    Extends the Adafruit LCD class to add features such as truncating long text.

    Works with the 2X16 monochrome LCD with i2c interface.

    Methods:
        display_text            writes two lines of text to the display
        clear_display           clears the display - faster than built-in clear method
        check_display_timeout   used in loops to timeout the backlight
        center_text             centers text, and truncates long text.  also makes sure text is ascii string
        clean_up                clears display, turns off backlight - used in error condtions.
    """""

    def __init__(self, timeout=5):
        # customize constructor, use superclass init
        Adafruit_CharLCDPlate.__init__(self)
        SonosUtils.__init__(self)
        self.timeout = timeout            # default backlight timeout
        self.display_start_time = time.time()

    def display_text(self, line1="", line2="", timeout=5, sleep=1):
        """"
        Displays two lines of text on the display display.

        Timeout keeps message displayed (seconds) unless something else gets displayed
        Sleep keeps message displayed even if something else trys to write to display, suspends other code except
        for interrupts (i think ?).  Some web comments suggest sleep of 1 is necessary, can't write to display
        faster than once per second.
        Also centers and truncates two lines of text
        if second line is 'nothing' replace with 16 spaces !
        """""
        try:
            self.timeout = timeout
            if line2 == 'nothing':
                line2 = "                "  # replace "nothing" keyword with 16 spaces (so display does not display garbage)
            # add spaces at front and rear
            line1 = SonosUtils.center_text(line1)
            line2 = SonosUtils.center_text(line2)
            # nxt check to see if last write was less than 2 seconds ago, if so sleep for 1 second
            #   as apparently these displays do not like to be written to more frequently than once a second.
            if time.time() - self.display_start_time < 2:
                time.sleep(1)
            self.set_backlight(1)
            # write each line individually, this might be better than inserting newline in one string? ( /n )
            self.set_cursor(0,0)
            self.message(line1)
            self.set_cursor(0,1)
            self.message(line2)
            # time.sleep(sleep)
            self.display_start_time = time.time()
            return
        except:
            # display is probably garbled, clear it
            #clear the display, apparantly this is faster than using the clear() method
            self.clear_display()
            print('unable to write to display')
            return

    def clear_display(self):
        """"
        clears the display, apparently this is faster than using clear function
        start at beginning of top row.  Have not timed it though.
        """""
        try:
            #start at beginning of top row
            self.set_cursor(0,0)
            # nxt print spaces, ie blanks
            self.message('                ')
            # nxt do it again for 2nd row
            self.set_cursor(0,1)
            self.message('                ')
        except:
            return

    def check_display_timeout(self):
        """"
        each time we write to display set a timer
        if nothing has reset the timer then turn off the backlight
        this has to run in a loop in the main program
        """""
        # set display timer
        display_on_time = time.time() - self.display_start_time
        if display_on_time > self.timeout:
            self.set_backlight(0)

    def clean_up(self):
        # clean up display on shutdown
        self.clear()
        self.set_backlight(0)

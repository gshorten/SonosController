

"""
The new circuitpy based modules for working with the Adafruit 2 line character display displays.

Classes:
    - ExtendedAdafruitI2CLCD      The adafruit display plate with buttons and i2c interface, is a subclass of adafruut moduls
"""

import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c
import time
import SonosUtils
import threading


class ExtendedAdafruitI2LCD(adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C):
    """
    Subclass of the adafruit i2c rgb display plate.

    This is a two line backlit LCD display.  Superclass is barebones so this class adds convienience methods
    for clearing display, setting backlight, centering and padding text.
    These methods are slghtly different from the character plate used in the volume box .

    The import is not aliased as the init of the superclass fails if an alias is used.
    Messy, but I did not know how to make it work otherwise.

    Methods:

        - display_text            displays two lines of text
        - clear_display           clears the display
        - check_display_timeout   times out the display
        - clean_up                cleans up the display on shutdown

    TODO add methods for reading the pushbuttons on the character plate (although the methods in the superclasses
        should work just fine, so this might not be necessary).
    """

    def __init__(self):
        """
        The init constants lcd_columns, lcd_rows,i2c are unlikely to change, although adafruit does make a 4 line
        display.  If I ever use that I will make those constants into parameters.
        """
        lcd_columns = 16
        lcd_rows = 2
        i2c = busio.I2C(board.SCL, board.SDA)
        super().__init__(i2c,lcd_columns,lcd_rows)
        self.display_start_time = time.time()
        # start timer def in seperate thread when instance is created.  This is so timing cycle using sleep
        # does not block execution of the program
        self.timer_thread = threading.Thread(target=self.display_timeout)
        self.timer_thread.start()
        self.color = [100,100,100]

    def is_busy(self, write_time = 2):
        """
        Checks to see if display is busy; returns True or False

        We need to check before writing to the display, as if you try to write while it is still writing
        the previous lines it gets garbled.
        :param write_time:      time required (worst case) for display to complete writing
        :type write_time:       int seconds
        :return:                True if display was last written to in less than write_time seconds
        :rtype:                 bool
        """
        if time.time() - self.display_start_time < write_time:
            return True
        else: return False

    def display_text(self, line1="  ", line2="  ", sleep=2):
        """
        Displays two lines of text on the display display.  Runs in it's own thread, an attempt to speed up display.

        :param line1:       first line of text
        :type line1:        str
        :param line2:       second line of text
        :type line2:        str
        :param sleep:       time to keep text displayed, in seconds
        :type sleep:        int

        Timeout keeps message displayed (seconds) unless something else gets displayed
        Sleep keeps message displayed even if something else trys to write to display, suspends other code except
        for interrupts (i think ?).  Some web comments suggest sleep of 1 is necessary, can't write to display
        faster than once per second.
        Also centers and truncates two lines of text
        if second line is 'nothing' replace with 16 spaces !
        """
        try:
            # make sure strings are utf-8, ignore characters that are not
            # so that we do not scramble the display

            line1 = str(line1)
            line2 = str(line2)
            if line2 == 'nothing':
                line2 = "                "
                # replace "nothing" keyword with 16 spaces (so display does not display garbage)
            # add spaces at front and rear
            line1 = SonosUtils.center_text(line1)
            line2 = SonosUtils.center_text(line2)
            # nxt check to see if last write was less than 2 seconds ago, if so sleep for 1 second
            #   as apparently these displays do not like to be written to more frequently than once a second.
            if self.is_busy():
                time.sleep(2)
            self.color = [100, 100, 100]
            # self.backlight = True
            self.clear()
            # self.set_cursor(0,0)
            # self.message = line1
            # set.cursor_position(0,1)
            # self.message = line2
            self.column_align = False
            text = line1 + '\n' + line2
            self.message = text
            time.sleep(sleep)
            self.display_start_time = time.time()
            return
        except:
            self.clear()
            print('unable to write to display - i2cCharLCD.display_text failed')
            return

    def display_timeout(self, timeout = 360):
        """
        Times out the display (turns off the backlight).  Starts when class instance is created.
        
        loops continuously, sleeping for 15 seconds at a time, then checks go see if 
        time from last display update exceeds the timeout variable.

        :param timeout:     turn off backlight after specified seconds
        :type timeout:      int
        """
        
        # do the time out loop here
        while True:
            elapsed = time.time() - self.display_start_time
            if elapsed >= timeout:
                self.color = [0, 0, 0]
                print('display has timed out, backlight is off')
            else:
                print('LCD timer, on time is: ', round(elapsed), ' seconds')
            #   self.color = [100, 100, 100]
            time.sleep(30)
        return

    def clean_up(self):
        """ Clean up display on shutdown."""
        self.clear()
        self.color = (0, 0, 0)

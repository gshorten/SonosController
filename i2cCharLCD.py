
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c
import time
import LCDUtils

"""
The new circuitpy based modules for working with the Adafruit 2 line character lcd displays.

Classes:
ExtendedAdafruitI2CLCD      The adafruit lcd plate with buttons and i2c interface, is a subclass of adafruut moduls
"""


class ExtendedAdafruitI2LCD(adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C):
    """
    Subclass of the adafruit i2c rgb lcd plate.

    This is a two line backlit LCD display.  Superclass is barebones so this class adds convienience methods
    for clearing display, setting backlight, centering and padding text.
    These methods are slghtly different from the character plate used in the volume box .

    The import is not aliased as the init of the superclass fails if an alias is used.
    Messy, but I did not know how to make it work otherwise.
    TODO fix this.

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
        # had to use the full path to the super classes to get the init to work
        adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C.__init__(self, i2c, lcd_columns, lcd_rows )
        #try the super() syntax instead - but this failed:
        #super().__init__(self,i2c,lcd_columns,lcd_rows)
        #set timer for the display timeout
        self.display_start_time = time.time()

    def display_text(self, line1="  ", line2="  ", sleep=1):
        """
        Displays two lines of text on the lcd display.

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
            if line2 == 'nothing':
                line2 = "                "  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)
            # add spaces at front and rear
            line1 = LCDUtils.center_text(line1)
            line2 = LCDUtils.center_text(line2)
            # nxt check to see if last write was less than 2 seconds ago, if so sleep for 1 second
            #   as apparently these displays do not like to be written to more frequently than once a second.
            if time.time() - self.display_start_time < 1:
                time.sleep(1)
            self.color = (100,0,0)
            text = line1 + '\n' + line2
            self.message = text
            time.sleep(sleep)
            self.display_start_time = time.time()
            return
        except:
            # display is probably garbled, clear it
            # clear the display, apparantly this is faster than using the clear() method
            self.clear_display()
            self.color = (0,0,0)
            print('unable to write to display - i2cCharLCD.display_text failed')
            return

    def clear_display(self):
        """
        Clears the LCD

        It's a method because the pi zero uses a different display module, and needs a different clear method.
        """
        try:
            self.clear()
        except:
            return

    def check_display_timeout(self, timeout = 60):
        """
        Times out the display (turns off the backlight).

        :param timeout:     turn off backlight after specified seconds
        :type timeout:      int

        Each time we write to display set a timer. if nothing has reset the timer then turn off the backlight.
        This has to run in a loop in the main program.
        """
        # calculate how long the display has been on
        display_on_time = time.time() - self.display_start_time
        if display_on_time > timeout:
            self.color(0 ,0 ,0)

    def clean_up(self):
        # clean up display on shutdown
        self.clear()
        self.color(0 ,0 ,0)
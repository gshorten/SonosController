
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as i2c_lcd
import LCDUtils
import time

"""
The new circuitpy based modules for working with the Adafruit 2 line character lcd displays.

Classes:
ExtendedAdafruitI2CLCD      The adafruit lcd plate with buttons and i2c interface
"""

class ExtendedAdafruitI2LCD(i2c_lcd, LCDUtils):
    """
    Subclass of the adafruit i2c 16X2 rgb lcd plate.

    Adds convienience methods for clearing display, setting backlight, centering and padding text
    These methods are slghtly different from the character plate used in the volume box .

    :param timeout:         time in seconds for backlight to turn off after displaying text
    :type timeout:          int
    :param lcd_columns:     width of lcd display, in characters
    :type lcd_columns:      int
    :param lcd_rows:        number of rows in the display
    :type lcd_rows:         int
    :param i2c:             initialiization string for the lcd
    :type i2c:              str  - do not fill, leave default

    Methods:

    display_text            displays two lines of text
    clear_display           clears the display
    check_display_timeout   times out the display
    clean_up                cleans up the display on shutdown

    to add: methods for reading the pushbuttons

    """


    def __init__(self, timeout=5, lcd_columns=16, lcd_rows=2):
        LCDUtils.LCD.__init__(self)
        i2c=busio.I2C(board.SCL, board.SDA)
        i2c_lcd.Character_LCD_RGB_I2C.__init__(i2c,lcd_columns,lcd_rows)
        self.timeout = timeout  # default backlight timeout
        self.display_start_time = time.time()

    def display_text(self, line1="", line2="", timeout=5, sleep=1):
        """
        Displays two lines of text on the lcd display.

        :param line1:       first line of text
        :type line1:        str


        Timeout keeps message displayed (seconds) unless something else gets displayed
        Sleep keeps message displayed even if something else trys to write to display, suspends other code except
        for interrupts (i think ?).  Some web comments suggest sleep of 1 is necessary, can't write to display
        faster than once per second.
        Also centers and truncates two lines of text
        if second line is 'nothing' replace with 16 spaces !


        """
        try:
            self.timeout = timeout
            if line2 == 'nothing':
                line2 = "                "  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)
            # add spaces at front and rear
            line1 = LCDUtils.LCD.center_text(line1)
            line2 = LCDUtils.LCD.center_text(line2)
            # nxt check to see if last write was less than 2 seconds ago, if so sleep for 1 second
            #   as apparently these displays do not like to be written to more frequently than once a second.
            if time.time() - self.display_start_time < 1:
                time.sleep(1)
            self.color(100 ,0 ,0)
            display_text = line1 + '/n' + line2
            self.message(display_text)
            # time.sleep(sleep)
            self.display_start_time = time.time()
            return
        except:
            # display is probably garbled, clear it
            # clear the display, apparantly this is faster than using the clear() method
            self.clear_display()
            print('unable to write to display')
            return

    def clear_display(self):
        """
        Clears the LCD
        """
        try:
            self.clear()
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
            self.color(0 ,0 ,0)

    def clean_up(self):
        # clean up display on shutdown
        self.clear()
        self.color(0 ,0 ,0)
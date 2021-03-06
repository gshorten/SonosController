
"""
Adafruit OLED Display
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import threading
import SonosUtils

class OLED:
    """
    Tiny little Adafruit OLED display
    Can display 2 - 4 number_of_lines of text, up to 16 characters wide with decent legibility.

    """
    def __init__(self, pixels_wide=128, pixels_high=32, font_size=14, lines=2, char_width = 18):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(pixels_wide, pixels_high, i2c)
        # First define some constants to allow easy resizing of shapes.
        self.font_size = font_size
        self.lines = lines
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        padding = -1
        self.top = padding
        self.bottom = self.height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0
        self.char_wide = char_width
        self.draw = ImageDraw.Draw(self.image)
        self.display_start_time = time.time()
        # start display time out loop in seperate thread
        self.timer_thread = threading.Thread(target=self.display_timeout)
        self.timer_thread.start()
        self.font = ImageFont.load_default()
        # todo add fonts to pi, for now use the default
        # self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf', self.font_size)
        # flag for determining if display is is_busy or not
        self.busy = False
        self.timed_out = False

    def clear_display(self):
        # Clear display.
        self.disp.fill(0)
        self.disp.show()
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(self.image)
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def display_text(self, line1, line2 = "", sleep=0):
        """
        Displays two strings.  If display is set up to show 3 number_of_lines, the first string is split over the first two
        number_of_lines.  If it is setup to display 4 number_of_lines, the first line is displayed on the first two number_of_lines, the second string
        is split up over the 3rd and 4th number_of_lines.
        :param line1:
        :type line1:
        :param line2:
        :type line2:
        :param sleep:
        :type sleep:
        :return:
        :rtype:
        """
        try:
            if self.busy:
                return
            self.busy = True
            line1 = SonosUtils.center_text(line1,self.char_wide)
            line2 = SonosUtils.center_text(line2,self.char_wide)
            self.clear_display()
            self.draw.text((self.x, self.top + 1),line1, font=self.font, fill=255)
            self.draw.text((self.x, self.top + self.font_size + 2), line2, font=self.font, fill=255)
            # Display image.
            self.disp.image(self.image)
            self.disp.show()
            self.display_start_time = time.time()
            time.sleep(sleep)
            self.busy = False
            self.timed_out = False

        except Exception as e:
            print(e)

    def display_timeout(self, timeout=600):
        """
        Times out the display (turns off the backlight).  Starts when class instance is created.

        loops continuously, sleeping for 15 seconds at a time, then checks go see if
        time from last display update exceeds the timeout variable.

        :param timeout:     turn off backlight after specified seconds
        :type timeout:      int
        """

        while True:
            elapsed = time.time() - self.display_start_time
            if elapsed >= timeout:
                self.clear_display()
                print('display has timed out, backlight is off')
                self.timed_out = True
            else:
                print('LCD timer, on time is: ', round(elapsed), ' seconds')
            time.sleep(15)
        return

    def is_busy(self):
        # Need this for compatibilty with slow displays that cannot be written to too quickly.
        return self.busy

    def display_time(self):
       pass

"""
Adafruit OLED Display
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import threading

class OLED:
    """
    Tiny little Adafruit OLED display
    """
    def __init__(self):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        self.disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
        # First define some constants to allow easy resizing of shapes.

        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))
        padding = -1
        self.top = padding
        self.bottom = self.height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0

        self.draw = ImageDraw.Draw(self.image)
        self.display_start_time = time.time()
        self.timer_thread = threading.Thread(target=self.display_timeout)
        self.timer_thread.start()

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

    def display_text(self, line1, line2 = ""):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf', 14)
        self.clear_display()
        self.draw.text((self.x, self.top + 0),line1, font=font, fill=255)
        self.draw.text((self.x, self.top + 15), line2, font=font, fill=255)
        # Display image.
        self.disp.image(self.image)
        self.disp.show()
        self.display_start_time = time.time()

    def is_busy(self):
        return False

    def display_timeout(self, timeout=360):
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
                # self.backlight = False
                print('display has timed out, backlight is off')
            else:
                print('LCD timer, on time is: ', round(elapsed), ' seconds')
            #   self.color = [100, 100, 100]
            time.sleep(30)
        return

    def check_display_timeout(self, timeout=300):
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
            self.clear_display()

    def clean_up(self):
        """ Clean up display on shutdown."""
        self.clear_display()

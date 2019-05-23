import time
import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

class OLED:
    """
    Tiny little Adafruit OLED display
    """
    def __init__(self):
        # Create the I2C interface.
        i2c = busio.I2C(SCL, SDA)

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

    def display_text(self, line1, line2):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf', 15)
        self.clear_display()
        self.draw.text((self.x, self.top + 0),line1, font=font, fill=255)
        self.draw.text((self.x, self.top + 15), line2, font=font, fill=255)
        # Display image.
        self.disp.image(self.image)
        self.disp.show()
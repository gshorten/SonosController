
"""
Adafruit OLED Display, 128 X 64
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import digitalio
import threading
import SonosUtils

class OLED:
    """
    Tiny little Adafruit OLED display
    Can display 2 - 4 number_of_lines of text, up to 16 characters wide with decent legibility.

    """
    def __init__(self, weather_updater, showing_weather = True, pixels_wide=128, pixels_high=32, font_size=14, lines=2, char_width = 26):
        # Create the I2C interface.
        i2c = busio.I2C(board.SCL, board.SDA)
        # Create the SSD1306 OLED class.
        # The first two parameters are the pixel width and pixel height.  Change these
        # to the right size for your display!
        reset_pin = digitalio.DigitalInOut(board.D20)
        self.disp = adafruit_ssd1306.SSD1306_I2C(pixels_wide, pixels_high, i2c, reset=reset_pin)
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
        # self.font = ImageFont.load_default()
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf', self.font_size)
        #self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf', self.font_size)
        # flag for determining if display is busy or not
        self.busy = False
        self.timed_out = False
        self.weather_updater = weather_updater
        self.showing_weather = showing_weather

    def clear_display(self):
        print('clearing the display')
        # Clear display.
        self.disp.fill(0)
        self.disp.show()
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.

        # Get drawing object to draw on image.
        draw = ImageDraw.Draw(self.image)
        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def display_text(self, line1, line2 = "", line3="", info = True, sleep=0):
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
                print("Display is busy")
            self.busy = True
            line1 = SonosUtils.center_text(line1,self.char_wide)
            line2 = SonosUtils.center_text(line2,self.char_wide)
            #infoline = time.strftime("%b %-d %-I:%M %p") +" "+ str(round(SonosUtils.get_cpu_temp()))+"c"
            if info:
                #print extra line of information - time and temperature
                infoline = time.strftime("%b %-d %-I:%M %p") + " " + SonosUtils.get_outside_temp() + "c"
                line3 = SonosUtils.center_text(infoline,self.char_wide)
            else:
                line3 = line3

            print("Updating Display")
            print(line1)
            print(line2)
            print(line3)
            self.clear_display()
            print('displaying lines on OLED')
            self.draw.text((self.x, self.top + 1),line1, font=self.font, fill=255)
            self.draw.text((self.x, self.top + self.font_size + 4), line2, font=self.font, fill=255)
            self.draw.text((self.x, self.top + 2*self.font_size + 8), line3, font=self.font, fill=255)
            # Display image.
            self.disp.image(self.image)
            self.disp.show()
            self.display_start_time = time.time()
            time.sleep(sleep)
            self.busy = False
            self.timed_out = False


        except Exception as e:
            print("Error writing to OLED display: ", e)

    def display_timeout(self, timeout=180):
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
                self.timed_out = True
                self.clear_display()
                print('display has timed out, backlight is off')
                if self.showing_weather:
                    # display weather for 30 seconds, then turn backlight off
                    weather_display = self.weather_updater.make_weather_disp(line_width=27)
                    print("showing weather display")
                    for i in weather_display:
                        print(i)
                    self.display.display_text(weather_display[0],weather_display[1],weather_display[2], info=False)
                    time.sleep(30)

            else:
                print('Display timer, on time is: ', round(elapsed), ' seconds')
            time.sleep(30)
        return

    def display_weather(self):
        """
        displays weather and time while display is timed out
        :return:
        :rtype:
        """



    def is_busy(self):
        # Need this for compatibilty with slow displays that cannot be written to too quickly.
        return self.busy

    def display_time(self):
       pass


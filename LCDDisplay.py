#!/usr/bin/env python
# Module containing methods for displaying info on the LCD Display

import time


class TwoLineLCD:
    # class for the adafruit two line lcd
    # methods for centering text, truncating text if it is too long
    #todo other fancy display methods (like scrolling) when I get around to it
    # lcd is LCD.Adafruit_CharLCDPlate()

    def __init__(self, lcd, line1, line2 = "nothing", duration = 0, display_timeout = 90):
        self.line1 = line1
        self.line2 = line2
        self.duration = duration
        self.lcd = lcd
        self.display_timeout = display_timeout
        self.display_started = time.time()
        # Initialize the LCD


    def lcd_display(self, line1, line2='nothing', duration=0):
        # displays two lines of text, sets display time out timer, turns on backlight
        # if second line is 'nothing' replace with 16 spaces !

        # check to see if line1 and line2 are valid ascii, avoid screwing up the display
        if  TwoLineLCD.is_ascii(self, self.line1) or TwoLineLCD.is_ascii(self, self.line2):
            display_started= time.time()
            self.lcd.set_backlight(.25)  # turn on the lcd backlight
            self.lcd.clear()  # clear whatever was on there before
            if len(line1) > 16:
                line1 = line1[:15]
            if len(line2) > 16:
                line2 = line2[:15]
            line1 = self.center_text(line1)
            line2 = self.center_text(line2)
            if line2 == 'nothing':
                line2 = "----------------"  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)

            text = str(line1) + '\n' + str(
                line2)  # make sure the two lines are strings, concatenate them, split to two lines
            self.lcd.message(text)
            # display on the LCD
            if duration > 0:
                time.sleep(duration)
            return
        else:
            # if not ascii text don't display anything
            self.lcd.message("")
            return

    def is_ascii(self,text):
        # checks to see if string is a valid ascii
        isascii = lambda text: len(text) == len(text.encode())
        return isascii

    def center_text(self,text):
        # centers text within 16 character length of the display
        text_length = len(text)
        padding = int(round((16 - text_length) / 2, 0))
        padding_text = " " * padding
        display_text = padding_text + text + padding_text
        return display_text

    def timeout_lcd(self):
        #turns off lcd backlight after timeout from start of last display of text

        if time.time() - self.display_started > self.display_timeout:
            self.lcd.set_backlight = 0
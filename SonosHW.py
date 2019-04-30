#!/usr/bin/env python

# Module for generic hardware bits used in my Sonos controllers - switches, displays, and rotary encoders
# but these could be used with any python project
# Classes for using an Adafruit RGB Rotary Encoder - has a push button, 2bit grey code rotary encoder, and RGB LED
# based on algorithm by Ben Buxton.  See his notes below.  minor modifications to include class for the LED
# and to remove un needed code
# note the Adafruit encoder needs the half step state table.

# Raspberry Pi Rotary Encoder Class
# $Id: rotary_class.py,v 1.7 2017/01/07 11:38:47 bob Exp $
#
# Copyright 2011 Ben Buxton. Licenced under the GNU GPL Version 3.
# Contact: bb@cactii.net
# Adapted by : Bob Rathbone and Lubos Ruckl (Czech republic)
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
#
# A typical mechanical rotary encoder emits a two bit gray code
# on 3 output pins. Every step in the output (often accompanied
# by a physical 'click') generates a specific sequence of output
# codes on the pins.
#
# There are 3 pins used for the rotary encoding - one common and
# two 'bit' pins.
#
# The following is the typical sequence of code on the output when
# moving from one step to the next:
#
#   Position   Bit1   Bit2
#   ----------------------
#     Step1     0      0
#      1/4      1      0
#      1/2      1      1
#      3/4      0      1
#     Step2     0      0
#
# From this table, we can see that when moving from one 'click' to
# the next, there are 4 changes in the output code.
#
# - From an initial 0 - 0, Bit1 goes high, Bit0 stays low.
# - Then both bits are high, halfway through the step.
# - Then Bit1 goes low, but Bit2 stays high.
# - Finally at the end of the step, both bits return to 0.
#
# Detecting the direction is easy - the table simply goes in the other
# direction (read up instead of down).
#
# To decode this, we use a simple state machine. Every time the output
# code changes, it follows state, until finally a full steps worth of
# code is received (in the correct order). At the final 0-0, it returns
# a value indicating a step in one direction or the other.
#
# It's also possible to use 'half-step' mode. This just emits an event
# at both the 0-0 and 1-1 positions. This might be useful for some
# encoders where you want to detect all positions.
#
# If an invalid state happens (for example we go from '0-1' straight
# to '1-0'), the state machine resets to the start until 0-0 and the
# next valid codes occur.
#
# The biggest advantage of using a state machine over other algorithms
# is that this has inherent debounce built in. Other algorithms emit spurious
# output with switch bounce, but this one will simply flip between
# sub-states until the bounce settles, then continue along the state
# machine.
# A side effect of debounce is that fast rotations can cause steps to
# be skipped. By not requiring debounce, fast rotations can be accurately
# measured.
# Another advantage is the ability to properly handle bad state, such
# as due to EMI, etc.
# It is also a lot simpler than others - a static state table and less
# than 10 lines of logic.

import RPi.GPIO as GPIO
import time
from Adafruit_CharLCD import Adafruit_CharLCDPlate


#todo can the following constants go in the RotaryEncoder class?
R_CCW_BEGIN = 0x1
R_CW_BEGIN = 0x2
R_START_M = 0x3
R_CW_BEGIN_M = 0x4
R_CCW_BEGIN_M = 0x5

# Values returned by 'process_'
# No complete step yet.
DIR_NONE = 0x0
# Clockwise step.
DIR_CW = 0x10
# Anti-clockwise step.
DIR_CCW = 0x20

R_START = 0x0

HALF_TAB = (
    # R_START (00)
    (R_START_M, R_CW_BEGIN, R_CCW_BEGIN, R_START),
    # R_CCW_BEGIN
    (R_START_M | DIR_CCW, R_START, R_CCW_BEGIN, R_START),
    # R_CW_BEGIN
    (R_START_M | DIR_CW, R_CW_BEGIN, R_START, R_START),
    # R_START_M (11)
    (R_START_M, R_CCW_BEGIN_M, R_CW_BEGIN_M, R_START),
    # R_CW_BEGIN_M
    (R_START_M, R_START_M, R_CW_BEGIN_M, R_START | DIR_CW),
    # R_CCW_BEGIN_M
    (R_START_M, R_CCW_BEGIN_M, R_START_M, R_START | DIR_CCW),
)

R_CW_FINAL = 0x1
R_CW_BEGIN = 0x2
R_CW_NEXT = 0x3
R_CCW_BEGIN = 0x4
R_CCW_FINAL = 0x5
R_CCW_NEXT = 0x6

FULL_TAB = (
    # R_START
    (R_START, R_CW_BEGIN, R_CCW_BEGIN, R_START),
    # R_CW_FINAL
    (R_CW_NEXT, R_START, R_CW_FINAL, R_START | DIR_CW),
    # R_CW_BEGIN
    (R_CW_NEXT, R_CW_BEGIN, R_START, R_START),
    # R_CW_NEXT
    (R_CW_NEXT, R_CW_BEGIN, R_CW_FINAL, R_START),
    # R_CCW_BEGIN
    (R_CCW_NEXT, R_START, R_CCW_BEGIN, R_START),
    # R_CCW_FINAL
    (R_CCW_NEXT, R_CCW_FINAL, R_START, R_START | DIR_CCW),
    # R_CCW_NEXT
    (R_CCW_NEXT, R_CCW_FINAL, R_CCW_BEGIN, R_START),
)

# Enable this to emit codes twice per step.
# HALF_STEP == True: emits a code at 00 and 11
# HALF_STEP == False: emits a code at 00 only
# GS - had to make this True to work with RGB encoder from adafruit
HALF_STEP = True
STATE_TAB = HALF_TAB if HALF_STEP else FULL_TAB

# State table has, for each state (row), the new state
# to set based on the next encoder output. From left to right in,
# the table, the encoder outputs are 00, 01, 10, 11, and the value
# in that position is the new state to set.


class RotaryEncoder:

    state = R_START
    pinA = None
    pinB = None
    CLOCKWISE = 1
    ANTICLOCKWISE = 2
    BUTTONDOWN = 4
    BUTTONUP = 3

    def __init__(self, pinA, pinB, button, callback_func):
        self.pinA = pinA
        self.pinB = pinB
        self.button = button
        self.callback_func = callback_func
        self.pin_state =0

        self.button_duration = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # The following lines enable the internal pull-up resistors
        # on version 2 (latest) boards
        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Add event detection to the GPIO inputs
        GPIO.add_event_detect(self.pinA, GPIO.BOTH, callback=self.rotary_event)
        GPIO.add_event_detect(self.pinB, GPIO.BOTH, callback=self.rotary_event)
        GPIO.add_event_detect(self.button, GPIO.BOTH, callback=self.button_event, bouncetime=50)

        self.button_down = 0
        self.button_timer = 0
        self.button_up = 0
        self.button_duration = ""


    def rotary_event(self, switch):
        # processes the interrupt
        # switch recieves the pin number triggering the event detect - we don't use it but it has to be in the def
        # Grab state of input pins.
        self.pin_state = (GPIO.input(self.pinB) << 1) | GPIO.input(self.pinA)
        # Determine new state from the pins and state table.
        self.state = STATE_TAB[self.state & 0xf][self.pin_state]
        # Return emit bits, ie the generated event.
        result = self.state & 0x30
        if result:
            event = self.CLOCKWISE if result == 32 else self.ANTICLOCKWISE
            # call the method that does something with event
            self.callback_func(event)
            print ('direction:',event)

    # Push button  event
    def button_event(self, button):
        if GPIO.input(button):
            event = self.BUTTONUP
        else:
            event = self.BUTTONDOWN
        self.callback_func(event=event)
        print("button:", event)
        return

    # Get a switch state
    def getSwitchState(self, switch):
        return GPIO.input(switch)

    # def get_button_press_duration(self, event):
    #     # determine if the button is pressed for a long or short press
    #     # return "short" or "long"
    #     if event == 3:
    #         self.button_down = time.time()
    #         return
    #     elif event == 4:
    #         self.button_up = time.time()
    #     self.button_timer = self.button_up - self.button_down
    #     if self.button_timer < .5:
    #         self.button_duration = "short"
    #     elif self.button_timer >= .5:
    #         self.button_duration = "long"
    #     print(self.button_duration, "button press")
    #     return self.button_duration

class KnobLED:
    # class to change the colour of the LED light on the knob
    # we might want to control this independently of the volume control so put it in a seperate class

    def __init__(self, green, red, blue):
        self.red = red
        self.green = green
        self.blue = blue
        # red,green, blue are the numbers of the GPIO pins
        # set GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # setup GPIO pins for LEDs on the encoder pushbutton
        GPIO.setup(self.green, GPIO.OUT)
        GPIO.output(self.green, GPIO.HIGH)
        GPIO.setup(self.red, GPIO.OUT)
        GPIO.output(self.red, GPIO.HIGH)
        GPIO.setup(self.blue, GPIO.OUT)
        GPIO.output(self.blue, GPIO.HIGH)

    def knob_led(self,on_off, colour='none', pause = 1):
        # turn encoder button light on and changes colour too.
        if on_off == 'off':
            GPIO.output(self.green, GPIO.HIGH)
            GPIO.output(self.red, GPIO.HIGH)
            GPIO.output(self.blue, GPIO.HIGH)
            return
        if on_off == 'on':
            if colour == 'green':
                pin = self.green
            elif colour == 'red':
                pin = self.red
            elif colour == 'blue':
                pin = self.blue
                time.sleep(pause)
                #todo take the pause out, it does not seem to do anything:(
                #   have to figure out a better way to show the blue LED for longer, right now it just flashes
                #   unless it takes sonos a while to change tracks, which sometimes happens.
                #   this is still useful as user knows that sonos is in a transition state
                #   note soco events module returns 3 states: playing, stopped, and transition (maybe a few more too)
            # finally, turn the led on.
            GPIO.output(pin, GPIO.LOW)
            return


class ExtendedLCD(Adafruit_CharLCDPlate):
     # extends the Adafruit LCD class to add features such as truncating long text, splitting into two lines,
     #  checking for ascii (display goes bonkers if it is not ascii)

    def __init__(self):
        # customize constructor, use superclass init
        Adafruit_CharLCDPlate.__init__(self)
        self.timeout = 5            # default duration
        self.display_start_time = time.time()

    def test_message(self):
        self.message("This is a test!")

    def display_text(self, line1="", line2="", timeout=5):
        # centers and truncates two lines of text, checks for valid ascii
        # if second line is 'nothing' replace with 16 spaces !
        # check to see if line1 and line2 are valid ascii, avoid screwing up the display
        self.timeout = timeout
        if self.is_ascii(line1) and self.is_ascii(line2):
            if len(line1) > 16:
                line1 = line1[:15]
            if len(line2) > 16:
                line2 = line2[:15]
            line1 = self.center_text(line1)
            line2 = self.center_text(line2)
            if line2 == 'nothing':
                line2 = "----------------"  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)
            text = str(line1) + '\n' + str(line2)  # make sure the two lines are strings,
                                                 # concatenate them, split to two lines
            self.clear()
            self.set_backlight(1)
            self.message(text)
            self.display_start_time = time.time()
        else:
            print('non ascii characters')
            return

    def check_display_timeout(self):
        display_on_time = time.time() - self.display_start_time
        if display_on_time > self.timeout:
            self.set_backlight(0)

    def is_ascii(self,text):
        # checks to see if string is a valid ascii. If AdaFruit lcd gets non ascii it goes bonkers.
        return all(ord(c) < 128 for c in text)

    def center_text(self,text):
        # centers text within 16 character length of the display
        text_length = len(text)
        padding = int(round((16 - text_length) / 2, 0))
        padding_text = " " * padding
        display_text = padding_text + text + padding_text
        return display_text

    def clean_up(self):
        self.clear()
        self.set_backlight(0)


class PushButton:
    # simple non-latching pushbutton
    def __init__(self, pin, callback):
        self.pin = pin
        GPIO.setup(pin, GPIO.IN)
        self.callback = callback
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.button_press, bouncetime=10)
        self.button_down_time = time.time()
        self.SHORT = .5


    def button_press(self,cb):
        press = GPIO.input(self.pin)
        print('Press:',press)
        if press:
            print
            #Button up
            event = "up"
            button_duration = time.time() - self. button_down_time
            if button_duration < self.SHORT:
                button_type = "short"
            else:
                button_type = "long"
        else:
            event = "down"
            self.button_down_time = time.time()
            print('down time: ',self.button_down_time)
            return
        print("channel: ",cb)
        self.callback(button_type)
        return





#!/usr/bin/env python
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
#

import RPi.GPIO as GPIO
import soco
import time

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
HALF_STEP = False
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
    BUTTONDOWN = 3
    BUTTONUP = 4

    #def __init__(self, pinA, pinB, s_unit, button, callback, revision):
    # took out the callback - i don't know how to use it :-(
    def __init__(self, pinA, pinB, button, callback, debounce, revision):
        self.pinA = pinA
        self.pinB = pinB
        self.button = button
        self.callback = callback
        self.debounce = debounce
        self.debounce_time_start = time.time()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if revision == 1:
            # For version 1 (old) boards
            GPIO.setup(self.pinA, GPIO.IN)
            GPIO.setup(self.pinB, GPIO.IN)
            GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            # The following lines enable the internal pull-up resistors
            # on version 2 (latest) boards
            GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Add event detection to the GPIO inputs
        GPIO.add_event_detect(self.pinA, GPIO.BOTH, callback=self.switch_event)
        GPIO.add_event_detect(self.pinB, GPIO.BOTH, callback=self.switch_event)
        GPIO.add_event_detect(self.button, GPIO.BOTH, callback=self.button_event, bouncetime=200)

    # Call back routine called by switch events
    def switch_event(self, switch):
        pulsetime = time.time() - self.debounce_time_start
        if pulsetime < self.debounce:
            self.debouncetimestart = time.time()
            print('short pulse:', pulsetime)
            return

        # Grab state of input pins.
        pinstate = (GPIO.input(self.pinB) << 1) | GPIO.input(self.pinA)
        # Determine new state from the pins and state table.
        self.state = STATE_TAB[self.state & 0xf][pinstate]
        # Return emit bits, ie the generated event.
        result = self.state & 0x30
        if result:
            event = self.CLOCKWISE if result == 32 else self.ANTICLOCKWISE
            self.callback(event)
            # print "Return: ",self.state & 0x30
            # return self.state & 0x30
            print ('direction:',event," pulsetime: ",pulsetime)
        self.debounce_time_start = time.time()

    # Push button up event
    def button_event(self, button):
        if GPIO.input(button):
            event = self.BUTTONUP
        else:
            event = self.BUTTONDOWN
        self.callback(event)
        print("button:", event)
        return

    # Get a switch state
    def getSwitchState(self, switch):
        return GPIO.input(switch)

def changevolume(event):
    new_volume = 0
    unit_volume = unit.volume
    if event == 1:
        # direction is clockwise
        new_volume = unit_volume + 3
        if new_volume > 100:
            new_volume = 100
        unit.volume = new_volume
    elif event == 2:
        # direction is counter clockwise, volume down
        new_volume = unit_volume - 3
        if new_volume < 0:
            new_volume = 0
        unit.volume = new_volume
    print ("new volume: ", new_volume)


unit = soco.SoCo('192.168.0.21')        # portable

VolControl = RotaryEncoder(19,26,4,changevolume, .0001, 2)

while True:
    try:
       pass
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
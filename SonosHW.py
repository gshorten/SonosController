
""""
Rasberry Pi UI Hardware

Module for generic hardware bits used in my Sonos raspberry pi controllers - switches, displays, and rotary encoders
but these could be used with any python project.

Classes:
    RotaryEncoder:  reads a standard 2-bit grey code encoder using threaded callback, passes CW or CCW to a callback
                    method for processing
    KnobLED:        controls a tricolour led - red, green, or blue
    ExtendedLCD:    subclass of the Adafruit_CharLCDPlate, which is a simple two line X 16 character LCD
    Pushbutton;     reads a standard momentary pushbutton using threaded callback, passes button press duration to
                    another callback method for processing
                    
I left debugging print statements in, line commented.

The rotary encoder class is based on a state machine algorithm by Ben Buxton (Thanks!).  
See his notes in the RotaryEncoder class.
"""""

import RPi.GPIO as GPIO
import time
from Adafruit_CharLCD import Adafruit_CharLCDPlate
import math


class RotaryEncoder:
    """"
    Rotary Encoder outputting 2 bit grey code.  Some encoders have a pushbutton and LED too, these are processed
    separate classes, although physically they are in the same device they have individual functions.

    Methods:
        rotary_event: uses threaded callback to read the GPIO pins on the rotary encoder.  calls  back a function
            defined in __init__ which is passed the result, which is either 'CW' for clockwise or
            'CCW' for counterclockwise
        getswitchstate: just gets the state of the GPIO pins, used in rotary_event

    This can be subclassed, although it's usually better to instance the rotary encoder as a separate object from
    the class containing the methods that process the output of the encoder, this is because you have to pass the
    processor class (instance) into the RotaryEncoder instance, sort of a chicken and egg scenario if you subclass the
    processor class.

    This uses an algorithm by Ben Buxton - many thanks, it works perfectly!
    I made minor modifications to include class for the LED, made the pushbutton a
    seperate class, changed variable names to make code more readable for my application,
    and to remove un-needed code.
    note the Adafruit encoder I used needs the half step state table.

    Ben Buxton notes below:

    Raspberry Pi Rotary Encoder Class
    $Id: rotary_class.py,v 1.7 2017/01/07 11:38:47 bob Exp $

    Copyright 2011 Ben Buxton. Licenced under the GNU GPL Version 3.
    Contact: bb@cactii.net
    Adapted by : Bob Rathbone and Lubos Ruckl (Czech republic)
    Site   : http://www.bobrathbone.com

    This class uses standard rotary encoder with push switch
    License: GNU V3, See https://www.gnu.org/copyleft/gpl.html

    Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
                The authors shall not be liable for any loss or damage however caused.


    A typical mechanical rotary encoder emits a two bit gray code
    on 3 output pins. Every step in the output (often accompanied
    by a physical 'click') generates a specific sequence of output
    codes on the pins.

    There are 3 pins used for the rotary encoding - one common and
    two 'bit' pins.

    The following is the typical sequence of code on the output when
    moving from one step to the next:

      Position   Bit1   Bit2
      ----------------------
        Step1     0      0
         1/4      1      0
         1/2      1      1
         3/4      0      1
        Step2     0      0

    From this table, we can see that when moving from one 'click' to
    the next, there are 4 changes in the output code.

    - From an initial 0 - 0, Bit1 goes high, Bit0 stays low.
    - Then both bits are high, halfway through the step.
    - Then Bit1 goes low, but Bit2 stays high.
    - Finally at the end of the step, both bits return to 0.

    Detecting the direction is easy - the table simply goes in the other
    direction (read up instead of down).

    To decode this, we use a simple state machine. Every time the output
    code changes, it follows state, until finally a full steps worth of
    code is received (in the correct order). At the final 0-0, it returns
    a value indicating a step in one direction or the other.

    It's also possible to use 'half-step' mode. This just emits an event
    at both the 0-0 and 1-1 positions. This might be useful for some
    encoders where you want to detect all positions.

    If an invalid state happens (for example we go from '0-1' straight
    to '1-0'), the state machine resets to the start until 0-0 and the
    next valid codes occur.

    The biggest advantage of using a state machine over other algorithms
    is that this has inherent debounce built in. Other algorithms emit spurious
    output with switch bounce, but this one will simply flip between
    sub-states until the bounce settles, then continue along the state
    machine.
    A side effect of debounce is that fast rotations can cause steps to
    be skipped. By not requiring debounce, fast rotations can be accurately
    measured.
    Another advantage is the ability to properly handle bad state, such
    as due to EMI, etc.
    It is also a lot simpler than others - a static state table and less
    than 10 lines of logic.
    """""

    # Define state tables
    # State table has, for each state (row), the new state
    # to set based on the next encoder output. From left to right in,
    # the table, the encoder outputs are 00, 01, 10, 11, and the value
    # in that position is the new state to set.

    # half tab state table
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

    # full tab state table
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
    HALF_STEP = False
    STATE_TAB = HALF_TAB if HALF_STEP else FULL_TAB

    state = R_START
    pinA = None
    pinB = None
    CLOCKWISE = 'CW'
    ANTICLOCKWISE = 'CCW'

    def __init__(self, pinA, pinB, rotary_callback):
        self.pinA = pinA                            # GPIO pins on pi for the rotary encoder - there are two
        self.pinB = pinB
        self.rotary_callback = rotary_callback      # def that processes rotary encoder
        self.pin_state =0
        self.button_timer = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # The following lines enable the internal pull-up resistors
        GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Add event detection to the GPIO inputs
        GPIO.add_event_detect(self.pinA, GPIO.BOTH, callback=self.rotary_event)
        GPIO.add_event_detect(self.pinB, GPIO.BOTH, callback=self.rotary_event)

    def rotary_event(self, switch):
        """"
        processes the interrupt
        switch recieves the pin number triggering the event detect - we don't use it but it has to be in the def
        """""
        # Grab state of input pins.
        self.pin_state = (GPIO.input(self.pinB) << 1) | GPIO.input(self.pinA)
        # Determine new state from the pins and state table.
        self.state = self.STATE_TAB[self.state & 0xf][self.pin_state]
        # Return emit bits, ie the generated event.
        result = self.state & 0x30
        # print("rotary result: ",result)
        if result:
            # result is either 32(CW), 0 (from both) or 16(CCW)
            direction = self.CLOCKWISE if result == 32 else self.ANTICLOCKWISE
            # call the method that does something with event
            self.rotary_callback(direction)
            #print ('direction:',direction)

    def getSwitchState(self, switch):
        return GPIO.input(switch)


class TriColorLED:
    """"
     RGB LED - configures an RGB led.
     
     Methods:
         change_led :       makes the led red, green, or blue
     """""

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

    def change_led(self, on_off, colour='none', pause = 1):
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
            elif colour == 'none':
                return
            # next turn the led on to the desired colour
            GPIO.output(pin, GPIO.LOW)
            return


class ExtendedLCD(Adafruit_CharLCDPlate):
    """"
    Extends the Adafruit LCD class to add features such as truncating long text.
    
    Works with the 2X16 monochrome LCD with i2c interface.
    
    Methods:
        display_text            writes two lines of text to the display
        clear_display           clears the display - faster than built-in clear method
        check_display_timeout   used in loops to timeout the backlight
        center_text             centers text, and truncates long text.  also makes sure text is ascii string  
        clean_up                clears display, turns off backlight - used in error condtions.  
    """""

    def __init__(self):
        # customize constructor, use superclass init
        Adafruit_CharLCDPlate.__init__(self)
        self.timeout = 5            # default backlight timeout
        self.display_start_time = time.time()

    def display_text(self, line1="", line2="", timeout=5, sleep=1):
        """"
        Displays two lines of text on the lcd display.
        
        Timeout keeps message displayed (seconds) unless something else gets displayed
        Sleep keeps message displayed even if something else trys to write to display, suspends other code except
        for interrupts (i think ?).  Some web comments suggest sleep of 1 is necessary, can't write to display
        faster than once per second.
        Also centers and truncates two lines of text
        if second line is 'nothing' replace with 16 spaces !
        """""
        try:
            self.timeout = timeout
            if line2 == 'nothing':
                line2 = "                "  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)
            # add spaces at front and rear
            line1 = self.center_text(line1)
            line2 = self.center_text(line2)
            # nxt check to see if last write was less than 2 seconds ago, if so sleep for 1 second
            #   as apparently these displays do not like to be written to more frequently than once a second.
            if time.time() - self.display_start_time < 1:
                time.sleep(1)
            self.set_backlight(1)
            # write each line individually, this might be better than inserting newline in one string? ( /n )
            self.set_cursor(0,0)
            self.message(line1)
            self.set_cursor(0,1)
            self.message(line2)
            # time.sleep(sleep)
            self.display_start_time = time.time()
            return
        except:
            # display is probably garbled, clear it
            #clear the display, apparantly this is faster than using the clear() method
            self.clear_display()
            print('unable to write to display')
            return

    def clear_display(self):
        """"
        clears the display, apparently this is faster than using clear function
        start at beginning of top row.  Have not timed it though.
        """""
        try:
            #start at beginning of top row
            self.set_cursor(0,0)
            # nxt print spaces, ie blanks
            self.message('                ')
            # nxt do it again for 2nd row
            self.set_cursor(0,1)
            self.message('                ')
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
            self.set_backlight(0)

    def center_text(self,text):
        """"
        centers text within 16 character length of the display
        also makes sure it is a string
        """""

        text_length = len(text)
        if text_length >16:
            # truncate text if it is too long
            # also convert to a string for good measure, in case we pass an object!
            text = str(text[0:15])
        # calculate how much padding is required to fill display
        padding = math.ceil((16 - text_length) / 2)
        padding_text = " " * (padding)
        # pad the display text to center it.
        display_text = padding_text + text + padding_text
        # make sure it is still 16 characters long; take the first 16 characters
        display_text = display_text[0:15]
        print('displaying text: ', display_text)
        return display_text

    def clean_up(self):
        # clean up display on shutdown
        self.clear()
        self.set_backlight(0)


class PushButton:
    """"
    Simple generic non-latching pushbutton.  
    
    Uses threaded callback from GPIO pins  to call button_press method
    
    Works with GPIO pins set to either pull up or pull down
    But, class assumes pi is setup for GPIO.BCM.  Saw no need to make this an attribute of the instance as
        BCM pin scheme seems to be universally used.

    Methods:
        button_press:   reads button, determines if button press is short or long, passes duration to callback method
    """""


    def __init__(self, button_pin, callback, short=1, bounce_time=50, gpio_up_down='down'):
        self.pin = button_pin                   #GPIO pin on
        self.gpio_up_down = gpio_up_down
        self.gpio_up_down = gpio_up_down
        self.callback = callback                # method that is called when button is pushed
        self.button_down_time = time.time()
        self.SHORT = short                      # duration of a short button press
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if self.gpio_up_down == 'up':
            GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif self.gpio_up_down == 'down':
            GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(button_pin, GPIO.BOTH, callback=self.button_press, bouncetime=bounce_time)

    def button_press(self,cb):
        """"
        Returns long or short button press, but is designed to send result
        to a callback function to take some action. 
        
        variable cb is the pin that fired, it is sent from the callback; we don't use it.
        """""
        # get the input from the gpio pin, it's either 0 or 1
        press = GPIO.input(self.pin)
        print('button press: ',press)
        if self.gpio_up_down == 'up':
            # if gpio pin is set for pull up then invert press, up is down and down is up :-)
            press = not press
            print('fixed press: ', press)
        if press:
            print("Button Down")
            # button is pushed down, start timer
            self.button_down_time = time.time()
            return
        elif press == False:
            print('Button Up')
            # Button up, calculate how long it was held down
            button_duration = time.time() - self. button_down_time
            if button_duration > self.SHORT:
                duration = "long"
            else:
                duration = "short"
            print(duration)
        # call method to process button press
        self.callback(duration)
        return





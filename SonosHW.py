
"""
Rasberry Pi UI Hardware.

Module for generic hardware bits used in my Sonos raspberry pi controllers - switches, displays, and rotary encoders
but these could be used with any python project.

Classes:
    - RotaryEncoder:  reads a standard 2-bit grey code encoder using threaded callback, passes CW or CCW to a callback
                    method for processing
    - KnobLED:        controls a tricolour led - red, green, or blue
    - Pushbutton;     reads a standard momentary pushbutton using threaded callback, passes button press duration to
                    another callback method for processing
                    
I left debugging print statements in, line commented.

The rotary encoder class is based on a state machine algorithm by Ben Buxton (Thanks!).  
See his notes in the RotaryEncoder class.
"""

import RPi.GPIO as GPIO
import time
import threading


class RotaryEncoder:
    """
    Rotary Encoder outputting 2 bit grey code.  Some encoders have a pushbutton and LED too, these are processed
    separate classes, although physically they are in the same device they have individual functions.

    Methods:
        - rotary_event: uses threaded callback to read the GPIO pins on the rotary encoder.  calls  back a function
            defined in __init__ which is passed the result, which is either 'CW' for clockwise or
            'CCW' for counterclockwise
        - getswitchstate: just gets the state of the GPIO pins, used in rotary_event

    This can be subclassed, although it's usually better to instance the rotary encoder as a separate object from
    the class containing the methods that process the output of the encoder, this is because you have to pass the
    processor class (instance) into the RotaryEncoder instance, sort of a chicken and egg scenario if you subclass the
    processor class.

    This uses an algorithm by Ben Buxton - many thanks, it works perfectly!
    I made minor modifications to include class for the LED, made the pushbutton a
    separate class, changed variable names to make code more readable for my application,
    and to remove un-needed code.

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
    """

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

    HALF_STEP = False
    STATE_TAB = HALF_TAB if HALF_STEP else FULL_TAB

    state = R_START

    CLOCKWISE = 'CW'
    ANTICLOCKWISE = 'CCW'

    def __init__(self, pinA, pinB, rotary_callback):
        """
        :param pinA:                Rotary encoder GPIO pin channel a
        :type pinA:                 int
        :param pinB:                Rotary encoder GPIO pin channel b
        :type pinB:                 int
        :param rotary_callback:     Method that processes the encoder output
        :type rotary_callback:      Method
        """
        self.state = 0
        self.pinA = pinA                            # GPIO pins on pi for the rotary encoder - there are two
        self.pinB = pinB
        self.rotary_callback = rotary_callback      # def that processes rotary encoder
        self.pin_state = 0
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
        """
        processes the interrupt
        switch recieves the pin number triggering the event detect - we don't use it but it has to be in the def
        """
        # Grab state of input pins.
        pin_state = (GPIO.input(self.pinB) << 1) | GPIO.input(self.pinA)
        # Determine new state from the pins and state table.
        self.state = self.STATE_TAB[self.state & 0xf][pin_state]
        # Return emit bits, ie the generated event.
        result = self.state & 0x30
        if result:
            # result is either 32(CW), 0 (from both) or 16(CCW)
            direction = self.CLOCKWISE if result == 32 else self.ANTICLOCKWISE
            # call the method that does something with event
            self.rotary_callback(direction)
            print ('direction:',direction)

    def getSwitchState(self, switch):
        return GPIO.input(switch)


class TriColorLED:
    """
     RGB LED - configures an RGB LED.

     :param green:  pin number for green led
     :type green:   int
     :param red:    pin number for red led
     :type  red:    int
     :param blue:   pin number for blue led
     :type  blue:   int

     Methods:
         - change_led :       makes the led red, green, or blue
     """

    def __init__(self, green=0, red=0, blue=0):
        """
        :param green:  GPIO pin number for green led
        :type green:   integer
        :param red:    GPIO pin for red led
        :type red:     integer
        :param blue:   GPIO pin for blue led
        :type blue:    integer
        """
        self.red = red
        self.green = green
        self.blue = blue
        # red,green, blue are the numbers of the GPIO pins
        # set GPIO mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # setup GPIO pins for LEDs on the encoder pushbutton
        GPIO.setup(self.green, GPIO.OUT)
        #GPIO.output(self.green, GPIO.HIGH)
        GPIO.setup(self.red, GPIO.OUT)
        #GPIO.output(self.red, GPIO.HIGH)
        GPIO.setup(self.blue, GPIO.OUT)
        #GPIO.output(self.blue, GPIO.HIGH)

    def change_led(self, on_off, colour='white', pause = 1):
        """
        Turn encoder button light on to a specific colour.

        The leds on the encoder need a common 3.3v supply, so GPIO pins have to be HIGH for off, LOW for on - they pull
        to ground to turn the leds on.

        :param on_off:      turn LED off
        :type on_off:       str
        :param colour:      color of LED to show
        :type colour:       str
        :param pause:       how long to sleep after turning LED on
        :type pause:        int
        :return:
        :rtype:

        TODO make this work both ways - add parameter to specify if output pins go HIGH or LOW.
        """

        if on_off == 'off':
            #Pull pins high, turn off LED
            GPIO.output(self.green, GPIO.HIGH)
            GPIO.output(self.red, GPIO.HIGH)
            GPIO.output(self.blue, GPIO.HIGH)

        elif on_off == 'on':
            # pull desired pins low (to ground) to turn leds on.
            if colour == 'green':
                GPIO.output(self.green, GPIO.LOW)
            elif colour == 'red':
                GPIO.output(self.red, GPIO.LOW)
            elif colour == 'blue':
                GPIO.output(self.blue,GPIO.LOW)
                time.sleep(pause)
            elif colour == 'white':
                # turn em all on
                GPIO.output(self.green, GPIO.LOW)
                GPIO.output(self.red, GPIO.LOW)
                GPIO.output(self.blue,GPIO.LOW)


class PushButtonAlt:
    """
    Simple generic non-latching pushbutton -  Alternate Algorithm, uses GPIO wait for edge method for button timing

    Works well in simple programs but generates segmentation faults under some situations.
    Uses threaded callback from GPIO pins  to call button_press method
    Todo try putting the edge detect into a separate thread, this might avoid the segmentation fault?

    Works with GPIO pins set to either pull up or pull down
    But, class assumes pi is setup for GPIO.BCM.  Saw no need to make this an attribute of the instance as
    BCM pin scheme seems to be universally used.

    Methods:
        - button_press:   reads button, determines if button press is short or long, passes duration to callback method
    """

    def __init__(self, button_pin, callback, long_press=750, debounce=25, gpio_up_down='up'):
        """
        :param button_pin:      GPIO pin for the raspberry pi input
        :type button_pin:       int
        :param callback:        method that does something with the output from the button (either 'short' or 'long')
        :type callback:         object ( name of method )
        :param long_press:      maximum duration, in ms, for a short press.  default works for most
        :type short:            int (milli seconds)
        :param debounce:        debounce argument for GPIO add_event_detect threaded callback.  Max should be ~50ms
        :type debounce:         int (milliseconds)
        :param gpio_up_down:    whether the GPIO pin on the raspberry pi is pulled up or down.  Used to initialize the
                                GPIO pins properly for the switch configuration.  Also, if 'up' we invert the input
                                so 1 still = down and 0 = up, so methods don't have to change depending on pin configurations
        :type gpio_up_down:     str
        """
        self.pin = button_pin
        self.gpio_up_down = gpio_up_down
        self.callback = callback
        self.long_press = long_press
        self.debounce = debounce

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        if self.gpio_up_down == 'up':
            GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.button_press, bouncetime=self.debounce)
        elif self.gpio_up_down == 'down':
            GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.button_press, bouncetime=self.debounce)

    def button_press(self, cb):
        """
        GPIO.remove_event causes a segmentation fault.... no one knows why.
        Gets a button press event from a button and determines if it is a short or long press.

        It is designed to send the result to a callback function to take some action
        depending how long the button is pressed.
        This algorithm triggers when a button is pushed (falling or rising, depending on how button is wired),
        then uses the gpio wait method to wait until the opposite event occurs, ie button is released.  Use the
        wait method timeout parameter to determine if the button is pressed for long or short.

        :param cb:     variable cb is the pin that fired, it is sent from the callback; we don't use it for anything.
        :type cb:      int ( BCM pin number )
        """

        # remove event detect so we can put GPIO wait function on same pin, to wait for button to come up
        GPIO.remove_event_detect(self.pin)
        GPIO.cleanup(self.pin)
        # handle both rising and falling - depends on if gpio pin on button is pulled high or low
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        if self.gpio_up_down == 'up':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            channel = GPIO.wait_for_edge(self.pin, GPIO.RISING, timeout=self.long_press)
        else:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            channel = GPIO.wait_for_edge(self.pin, GPIO.FALLING, timeout=self.long_press)
        if channel is None:
            # if we don't get an edge detect within the long press time out then it's automatically a long press
            # callback the function that processes the button press, pass parameter long or short
            # not very pythonic (should use a binary) but easier to read.
            print('long press')
            duration = 'long'
        else:
            duration = 'short'
            print('short press')

        # remove the wait edge detect we put on the button pin
        GPIO.remove_event_detect(self.pin)
        GPIO.cleanup(self.pin)
        # and add back the appropriate interrupt, for if the pin is falling or rising.
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        if self.gpio_up_down == 'up':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.button_press, bouncetime=self.debounce)
        else:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.button_press, bouncetime=self.debounce)
        self.callback(duration)

class PushButton:
    """
    Simple generic non-latching pushbutton.  This is stable, use this class.
    
    Uses threaded callback from GPIO pins  to call button_press method
    
    Works with GPIO pins set to either pull up or pull down
    But, class assumes pi is setup for GPIO.BCM.  Saw no need to make this an attribute of the instance as
    BCM pin scheme seems to be universally used.

    Methods:
        - button_press:   reads button, determines if button press is short or long, passes duration to callback method
    """

    def __init__(self, button_pin, callback, long_press=.75, debounce=25, gpio_up_down='up'):
        """
        :param button_pin:      GPIO pin for the raspberry pi input
        :type button_pin:       int
        :param callback:        method that does something with the output from the button (either 'short' or 'long')
        :type callback:         object ( name of method )
        :param long_press:      maximum duration, in seconds, for a short button press.  default works for most
        :type long_press:       int (seconds)
        :param debounce:        debounce argument for GPIO add_event_detect threaded callback.  Max should be ~50ms
        :type debounce:         int (milliseconds)
        :param gpio_up_down:    whether the GPIO pin on the raspberry pi is pulled up or down.  Used to initialize the
                                GPIO pins properly for the switch configuration.  Also, if 'up' we invert the input
                                so 1 still = down and 0 = up, so methods don't have to change depending on pin configurations
        :type gpio_up_down:     str
        """
        self.pin = button_pin
        self.gpio_up_down = gpio_up_down
        self.callback = callback
        self.long_press = long_press
        self.debounce = debounce
        self.button_timer = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # set up gpio pins for interrupt, accomodating pins pulled high or low.
        if self.gpio_up_down == 'up':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        elif self.gpio_up_down == 'down':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.pin, GPIO.BOTH, callback=self.button_press, bouncetime=self.debounce)

    def button_press(self, cb):
        """
        Gets a button press event from a button and determines if it is a short or long press.

        It is designed to send the result to a callback function to take some action
        depending how long the button is pressed.
        This algorithm triggers when a button is pushed (falling or rising, depending on how button is wired),
        then uses the gpio wait method to wait until the opposite event occurs, ie button is released.  Use the
        wait method timeout parameter to determine if the button is pressed for long or short.

        :param cb:     variable cb is the pin that fired, it is sent from the callback; we don't use it for anything.
        :type cb:      int ( BCM pin number )
        """
        # get press event
        push = GPIO.input(self.pin)
        # down is 1 (true)
        if self.gpio_up_down == "up":
            #if GPIO pin is pulled down, then pushing button down will pull pin high, so 1 = button going down
            #if GPIO pin is pulled up, this is reversed, but we want 1 for the code below, so we reverse it.
            push = not push
        print ('button push : ',push)
        if push == 0:
            # if push == 0 button is coming back up
            duration = time.time() - self.button_timer
            if duration > self.long_press:
                print('long press: ' ,duration)
                short_long = 'long'
            else:
                short_long = 'short'
                print('short press: ',duration)
            self.callback(short_long)
            return
        elif push == 1:
            self.button_timer = time.time()
            return


class DoublePushButton:
    """
    Simple generic non-latching pushbutton. Returns single or double press to a callback function

    Uses threaded callback from GPIO pins  to call button_press method

    Works with GPIO pins set to either pull up or pull down
    But, class assumes pi is setup for GPIO.BCM.  Saw no need to make this an attribute of the instance as
    BCM pin scheme seems to be universally used.

    Methods:
        - button_press:   reads button, determines if button press is short or long, passes duration to callback method
    """

    def __init__(self, button_pin, callback, double_press=.5, debounce=25, gpio_up_down='up'):
        """
        :param button_pin:      GPIO pin for the raspberry pi input
        :type button_pin:       int
        :param callback:        method that does something with the output from the button (either 'short' or 'long')
        :type callback:         object ( name of method )
        :param long_press:      maximum duration, in seconds, for a short button press.  default works for most
        :type long_press:       int (seconds)
        :param debounce:        debounce argument for GPIO add_event_detect threaded callback.  Max should be ~50ms
        :type debounce:         int (milliseconds)
        :param gpio_up_down:    whether the GPIO pin on the raspberry pi is pulled up or down.  Used to initialize the
                                GPIO pins properly for the switch configuration.  Also, if 'up' we invert the input
                                so 1 still = down and 0 = up, so methods don't have to change depending on pin configurations
        :type gpio_up_down:     str
        """
        self.pin = button_pin
        self.gpio_up_down = gpio_up_down
        self.callback = callback
        self.double_press = double_press
        self.debounce = debounce
        self.previous_press = time.time()
        self.first_press = True
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # set up gpio pins for interrupt, accomodating pins pulled high or low.
        if self.gpio_up_down == 'up':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.button_press, bouncetime=self.debounce)
        elif self.gpio_up_down == 'down':
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.button_press, bouncetime=self.debounce)

    def button_press(self, cb):
        """
        Gets a button press event from a button and determines if it is a short or long press.

        It is designed to send the result to a callback function to take some action
        depending how long the button is pressed.
        This algorithm triggers when a button is pushed (falling or rising, depending on how button is wired),
        then uses the gpio wait method to wait until the opposite event occurs, ie button is released.  Use the
        wait method timeout parameter to determine if the button is pressed for long or short.

        :param cb:     variable cb is the pin that fired, it is sent from the callback; we don't use it for anything.
        :type cb:      int ( BCM pin number )
        """

        time_from_last = time.time() - self.previous_press
        if time_from_last < self.double_press:
            type = 'accept'
            print('double press: ', time_from_last)

            time.sleep(.5)
        else:
            # single press
            type = 'select'
            print("single press", time_from_last)

            self.callback(type)

class SinglePressButton():
    def __init__(self, pin, callback, gpio_up = 1, debounce = 1500):
        self.debounce = debounce
        self.gpio_up = gpio_up
        self.pin = pin
        self.callback = callback
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        # set up gpio pins for interrupt, accomodating pins pulled high or low.
        if self.gpio_up:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.button_press, bouncetime=self.debounce)
        elif not self.gpio_up:
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.button_press, bouncetime=self.debounce)

    def button_press(self,cb):
        self.callback()


class WallBox:
    """
    Interface to the Seeburg WA-200 Jukebox wallbox.  Decodes the output of the wallbox into a number 0 - 199

    The Seeburg wallbox makes a selection with a combination of a letter press (A - V, excluding I, O, as these
    could be confused with numbers 1 and 0), for a total of 20 letters, and one of 10 numbers (1- 9,0).  The two
    combined totals 200 possible selections.

    The output from the wallbox is 24v ac pulses, 4-5 ac cycles per pulse.  These signals are sent to a Fairchild
    MID 400 AC line sensing chip which converts them to a 5v logic signal.   The signal from the chip is +5v, when it
    sees 24v ac it pulls the output to ground and latches until the ac signal has stopped.  Perfect square waves.  The
    5v is dropped to 3.3v with a voltage divider.

    The processed signal from the wallbox looks like this:
                                                                                                |
    +5v --------|          |---------|                        |----------|         |------------|-----------
                |          |         |                        |          |         |            |
                |          |         |                        |          |         |            |
                |          |         |                        |          |         |        occasional noise
    0v          -----------          -------------------------           -----------
                ^  ~42ms   ^  ~36ms  ^        ~220ms          ^
                ^ ~78ms edge to edge ^     ~260 - 270 ms edge to edge    ^

                ^ start letters      ^     gap between        ^start numbers               finished - no more edges
                                         letters & numbers

    Sometimes we get a noise spike about 500ms after the last pulse,
    it is very short - 1-2 ms, so we have to remove this in software, as the pi will read it.

    Definitions:
        - pulse beginning:      the start of a pulse, falling from 3.3v to 0
        - pulse:                a single pulse from falling edge to next falling edge

    Methods:
        - pulse_count           Threaded callback when buttons are pressed on the wallbox. Counts the letters and
                                numbers pressed
        - wait_for_pulses_end   loops waiting for last pulse from wallbox.
        - convert_wb            converts the letter and number selection into a number 0- 199
    """

    # constants for detecting and decoding wallbox pulses
    LETTER_MAX = .275       # minimum and maximum gap between letters and numbers
    LETTER_MIN = .260
    PULSE_MAX = .085        # maximum duration of a letter or number pulse
    PULSE_MIN = .070        # minimum duration of a letter or number pulse
    DEBOUNCE = 20           # don't need a big debounce - maybe not at all, signal is clean

    def __init__(self, pin, callback):
        """
        :param pin:         GPIO pin for the wallbox input.
        :type pin:          int
        :param callback:    name of the method that does something with the wallbox pulses
        :type callback:     object (method name)
        """
        self.pin = pin                      # used to be gpio 20, will change
        self.callback = callback
        self.first_pulse = True
        self.last_pulse_start = 0
        self.counting_numbers = False
        self.letter_count = 0
        self.number_count = 0
        self.pulse_start_time = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.IN)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=self.DEBOUNCE)
        GPIO.add_event_callback(self.pin, self.pulse_count)
        # GPIO pin has +3 volts on it, the Fairchild MID 400 AC line sensing chip pulls this to ground
        # when a wallbox pulse starts, so we want to trigger the callback on the falling edge.

    def pulse_count(self,cb):
        """
        Counts the pulses from the wallbox, first the letters, then the numbers.  Filters out stuff that is not a
        valid pulse.
        """
        # get the time the pulse started
        # self.pulse_started = True
        self.pulse_start_time = time.time()
        # calculate the duration from the last pulse
        duration = time.time() - self.last_pulse_start
        print('duration: ', round(duration, 3))
        # next check to see if it is a valid pulse, ie not noise, or the very long pulse between sets of pulses
        # if either a regular pulse or the gap between letters and numbers then start (or continue) counting
        # this filters out any short duration noise spikes, which usually occur after pulses are finished.

        if self.first_pulse:
            # if it is the first pulse then don't count it yet, just record the time of the pulse,
            print('******************* PULSES STARTED ***********************')
            # reset first pulse flag
            self.first_pulse = False
            # run method to wait for the end of pulse train in separate thread
            pulses_end = threading.Thread(target=self.wait_for_pulses_end)
            pulses_end.start()
        elif self.LETTER_MAX > duration > self.LETTER_MIN or self.PULSE_MAX > duration > self.PULSE_MIN:
            # print('valid pulse')
            # check for gap between the letters and numbers
            if self.LETTER_MAX > duration > self.LETTER_MIN:
                # if it matches the letter-number gap flag that we are now counting numbers, not letters
                self.counting_numbers = True
                print('================Now counting numbers ====================')
            else:
                if not self.counting_numbers:
                    # we are counting letters
                    self.letter_count += 1
                    print('Letter count: ', str(self.letter_count))
                else:
                    self.number_count += 1
                    print('Number count: ', str(self.number_count))

        # record the time of this pulse
        self.last_pulse_start = self.pulse_start_time
        return

    def wait_for_pulses_end(self):
        """
        Runs in a separate thread when  wallbox pulses start.  Pulse train lasts a maximum of 3 seconds.
        When it is finished, call whatever method that does something with the pulses.

        Also reset class counters and flags for next train of pulses.
        """

        # wait 3 seconds for the set of wallbox pulses to end (3 seconds is max duration for a series of pulses)
        time.sleep(3.5)
        print("**************  Pulses Ended ***********")
        print("Letter Count: ", self.letter_count)
        print("Number Count: ", self.number_count)

        # get the number of the selection
        selection = self.convert_wb(self.letter_count, self.number_count)
        print("wallbox selection number is: ", selection)

        # reset flags and counters
        self.first_pulse = True
        self.letter_count = 0
        self.number_count = 0
        self.counting_numbers = False

        # call the method that processes the wallbox selection
        self.callback(selection)
        return


    def convert_wb(self,letter, number):
        """
        Turns letter and number into a single number 0-199.

        It's a base 20 system; with the letters being numbers 0-19, then the number being the "20"'s digit,
        so we have to multply the number by 20 then add the letter to it.  Number is the first digit, letter the second,
        although on the wallbox the letter is selected first, number second.

        Pulse detect algorithm returns numbers in range 0-9, letters in range 1 - 20; we adjust letters down by one so
        that they are in the range 0-19 (ie, 'A' is 0, not 1)

        Examples:  wallbox selection is "B3", letter is 2, number is 3 = (3*20) +  (2-1) = 61
                   wallbox selection is "A0", letter is 1, number is 9 = (19*20) + (1-1) = 180

        :param letter:      Number representing the letter pressed on the wallbox (0- 19)
        :type letter:       int
        :param number:      Number representing the number key pressed on the wallbox (0-9)
        :type number:       int
        """

        #  Adjust the letter and number count to get the right tracks
        #  because we look these up by index, python indexes start at 0, so we subtract 1 from letter count

        letter -= 1
        number = (number) * 20
        # it's a base 20 system; with the letters being numbers 0-19, then the number being the "20"'s digit
        # so we have to multply the number by 20 then add the letter to it
        # we add 1 to the number because with this algorithm the last pulse is not counted
        conversion = letter + number + 1
        print("Conversion is: ", conversion)
        return conversion




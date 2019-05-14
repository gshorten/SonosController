"""
 notes in the RotaryEncoder class.
"""

import RPi.GPIO as GPIO
import time



class PushButton:
    """
    Simple generic non-latching pushbutton.

    Uses threaded callback from GPIO pins  to call button_press method

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
        DO NOT USE  GPIO.remove_event causes a segmentation fault.... no one knows why.
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
        # handle both rising and falling - depends on if gpio pin on button is pulled high or low
        if self.gpio_up_down == 'up':
            # wait for the button to come up, using edge detect.
            channel = GPIO.wait_for_edge(self.pin, GPIO.RISING, timeout=self.long_press)
        else:
            channel = GPIO.wait_for_edge(self.pin, GPIO.FALLING, timeout=self.long_press)
        if channel is None:
            # if we don't get an edge detect within the long press time out then it's automatically a long press
            # callback the function that processes the button press, pass parameter long or short
            # not very pythonic (should use a binary) but easier to read.
            print('long press')
            duration = 'long'
        else:
            duration = 'short'
            print('long press')
        self.callback(duration)
        # remove the wait edge detect we put on the button pin
        GPIO.remove_event_detect(self.pin)
        GPIO.cleanup(self.pin)
        # and add back the appropriate interrupt, for if the pin is falling or rising.
        if self.gpio_up_down == 'up':
            GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.button_press, bouncetime=self.debounce)
        else:
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self.button_press, bouncetime=self.debounce)



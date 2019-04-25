#!/usr/bin/env python

# Module with generic classes for controlling sonos system with raspberry pi + rotary encoders, switches, lcd displays, etc
#

import soco
import time
import RGBRotaryEncoder

class PlaystateLED:
    # class to change the sonos volume rotary controller's LED depending on play_state and other things
    # but right now only can think of playstate
    # made it a class in case I think of other unit related things to show on the knob, like is unit in the current
    # group?

    def __init__(self, unit, led):
        self.unit = unit            #sonos unit we are checking for
        self.led = led              #led object on rotary controller

    def play_state_LED(self):
        # changes colour of light on encoder button depending on play state of the sonos unit
        unit_state = self.unit.get_current_transport_info()
        # time.sleep(.05)  # pause long enough for sonos to respond
        # todo play with this, we might not need it
        # determine if the sonos unit is playing or not
        play_state = unit_state['current_transport_state']
        if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
            # change the colour of the led
            # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
            self.led.knob_led('off', 'green')
            self.led.knob_led('on', 'red')
        elif play_state == "PLAYING":
            self.led.knob_led('off', 'red')
            self.led.knob_led('on', 'green')

        return
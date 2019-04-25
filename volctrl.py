#!/usr/bin/env python
import RGBRotaryEncoder
import SonosControl
import RPi.GPIO as GPIO
import soco
import time
# import Adafruit_CharLCD as LCD

# this is morphing into my new OOP based volume control
# RGBRotaryEncoder is a class for a generic RGB Rotary Encoder.

# NOTE I had to edit soco core.py module to fix group discovery to make by_name and other functions work
# see patch file text below... i manually edited "for group_element in tree.findall('ZoneGroup')
# and replaced it with the following patch line.  This fixed discovery methods.
# --- soco/core.py	(revision 671937e07d7973b78c0cbee153d4f3ad68ec48c6)
# +++ soco/core.py	(date 1554404884029)
# @@ -949,7 +949,7 @@
#          self._all_zones.clear()
#          self._visible_zones.clear()
#          # Loop over each ZoneGroup Element
# -        for group_element in tree.findall('ZoneGroup'):
# +        for group_element in tree.find('ZoneGroups').findall('ZoneGroup'):
#              coordinator_uid = group_element.attrib['Coordinator']
#              group_uid = group_element.attrib['ID']
#              group_coordinator = None
# ------------------------ Class definitions ------------------------------------

class SonosVolCtrl():
    # processes the callback from the rotary encoder to change the volume of the sonos unit
    # and does stuff when the encoder button is pressed (also via callbacks)

    def __init__(self, sonos_unit, vol_ctrl_led, up_increment = 4, down_increment = 5,):
        # sonos unit
        self.unit = sonos_unit
        self.upinc = up_increment       # how much to change the volume each click of the volume knob
        self.downinc = down_increment   # how much to change the volume down
        self.vol_ctrl_led = vol_ctrl_led

    def change_volume(self,event):
        # callback function to change the volume of the sonos unit
        # is called from the RotaryEncoder class
        # event is returned from the RotaryEncoder class, can be either 1(clockwise rotation) or 2 (counter cw)
        new_volume = 0
        # get the volume of the sonos unit
        unit_volume = self.unit.volume
        # increment the volume up or down based on event value
        # also limit volume to between 0 and 100
        if event == 1:
            # direction is clockwise
            new_volume = unit_volume + self.upinc
            if new_volume > 100:
                new_volume = 100
            self.unit.volume = new_volume
            print("new volume: ", new_volume)
        elif event == 2:
            # direction is counter clockwise, volume down
            # turn volume down more quickly than up, better for the user!
            new_volume = unit_volume - self.downinc
            if new_volume < 0:
                new_volume = 0
            self.unit.volume = new_volume
            print ("new volume: ", new_volume)

        elif event == 3 or event ==4:
            # these events are the rotary encoder button being pressed.
            # 3 is down, 4 is up
            # use a seperate def to figure out short or long press.
            if RGBRotaryEncoder.RotaryEncoder.get_button_press_duration(self,event) == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif RGBRotaryEncoder.RotaryEncoder.get_button_press_duration(self,event) == "long":
                try:
                    # long button press, skip to the next track
                    self.vol_ctrl_led.knob_led('off')
                    self.vol_ctrl_led.knob_led('on', 'blue')
                    print("Skipping to next track")
                    self.unit.next()
                except:
                    print("cannot go to next track with this source")


    def pause_play(self):
        # pauses or plays the sonos unit, toggles between the two.
        play_state = self.unit.get_current_transport_info()['current_transport_state']
        print(play_state)
        if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
            self.unit.play()
            print("Now Playing")
        elif play_state == "PLAYING":
            # unit is playing, stop it
            self.unit.pause()
            print("Now Paused")


# class PlaystateLED:
#     # class to change the sonos volume rotary controller's LED depending on play_state and other things
#     # but right now only can think of playstate
#     # made it a class in case I think of other unit related things to show on the knob, like is unit in the current
#     # group?
#
#     def __init__(self, unit, led):
#         self.unit = unit            #sonos unit we are checking for
#         self.led = led              #led object on rotary controller
#
#     def play_state_LED(self):
#         # changes colour of light on encoder button depending on play state of the sonos unit
#         unit_state = self.unit.get_current_transport_info()
#         # time.sleep(.05)  # pause long enough for sonos to respond
#         # todo play with this, we might not need it
#         # determine if the sonos unit is playing or not
#         play_state = unit_state['current_transport_state']
#         if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
#             # change the colour of the led
#             # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
#             self.led.knob_led('off', 'green')
#             self.led.knob_led('on', 'red')
#         elif play_state == "PLAYING":
#             self.led.knob_led('off', 'red')
#             self.led.knob_led('on', 'green')
#
#         return

# -------------------------- Main part of program -------------------

# assign sonos player to unit object
# unit = soco.SoCo('192.168.0.21')        # portable
#todo use a second rotary control to select sonos units!
# for now it is hard coded :-(


unit = soco.discovery.by_name("Garage")
print(unit, unit.player_name)

# create LED for the volume knob
VolCtrlLED = RGBRotaryEncoder.KnobLED(green=22, red=27, blue=17)

# create play state change LED object
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VolCtrl_PlaystateLED = SonosControl.PlaystateLED(unit,VolCtrlLED)


# This changes the volume of the sonos unit
# contains the callback method called by the PiZeroEncoder object
# it's not called directly, but via the callback when the volume knob is turned (or pushed)
PiZeroSonosVolumeKnob = SonosVolCtrl(unit, VolCtrlLED, up_increment=4, down_increment=5)

# create rotary encoder instance, it decodes the rotary encoder and generates the callbacks for the VolumeKnob
PiZeroEncoder = RGBRotaryEncoder.RotaryEncoder(pinA=19, pinB=26, button=4, callback=PiZeroSonosVolumeKnob.change_volume)


while True:
    try:
        VolCtrl_PlaystateLED.play_state_LED()
        # change LED knob LED depending on play state
        # the volume control triggers methods based on interrupts, changing the colour of the LED has to be polled in
        # in the main program loop
        #todo see if we can use soco.events to trigger light change with a callback function.
        # but probably unecessary as this method is faster than the sonos app on phone :-)
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit

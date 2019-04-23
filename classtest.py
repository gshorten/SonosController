#!/usr/bin/env python
import RGBRotaryEncoder as Encoder
import RPi.GPIO as GPIO
import soco
import time

class SonosVolCtrl:
    # processes the callback from the rotary encoder to change the volume of the sonos unit
    # and does stuff when the encoder button is pressed.

    def __init__(self, sonos_unit, up_increment = 4, down_increment = 5):
        # sonos unit
        self.unit = sonos_unit
        self.upinc = up_increment   # how much to change the volume each click of the volume knob
        self.downinc = down_increment   #how much to change the volume down
        self.button_down = 0
        self.button_timer = 0
        self.button_up = 0
        self.button_type = ""

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
            if self.button_press_duration(event) == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif self.button_press_duration(event) == "long":
                # long button press, skip to the next track
                self.unit.next()

    def button_press_duration(self,press):
        # determine if the button is pressed for a long or short press
        # return "short" or "long"
        if press == 3:
            self.button_down = time.time()
            return
        elif press == 4:
            self.button_up = time.time()
        self.button_timer = self.button_up - self.button_down
        if self.button_timer < .5:
            self.button_type = "short"
        elif self.button_timer >= .5:
            self.button_type = "long"
        print(self.button_type, "button press")
        return self.button_type

    def pause_play(self):
        # pauses or plays the sonos unit
        play_state = self.unit.get_current_transport_info()['current_transport_state']
        print(play_state)
        if play_state == "PAUSED" or play_state == "STOPPED":
            self.unit.play()
            print("Now Playing")
        elif play_state == "PLAYING":
            # unit is playing, stop it
            self.unit.pause()
        print("Now Paused")

# assign sonos player to unit object
# unit = soco.SoCo('192.168.0.21')        # portable

unit = soco.discovery.by_name("Portable")
print(unit, unit.player_name)

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


# create sonos volume control knob instance
VolumeKnob = SonosVolCtrl(unit, up_increment=4, down_increment=5)
# create rotary encoder instance
RotaryVol = Encoder.RotaryEncoder(19, 26, 4, VolumeKnob.change_volume)

while True:
    try:
       pass
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
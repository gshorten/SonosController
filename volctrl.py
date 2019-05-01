#!/usr/bin/env python
import SonosHW                  # has the hardware bits - rotary encoder, lcd, etc
import SonosControl             # has classes for controlling the sonos system
import RPi.GPIO as GPIO
import time

'''
This is morphing into my new OOP based volume control

NOTE I had to edit soco core.py module to fix group discovery to make by_name and other functions work
see patch file text below... i manually edited "for group_element in tree.findall('ZoneGroup')
and replaced it with the following patch line.  This fixed discovery methods.
--- soco/core.py	(revision 671937e07d7973b78c0cbee153d4f3ad68ec48c6)
+++ soco/core.py	(date 1554404884029)
@@ -949,7 +949,7 @@
         self._all_zones.clear()
         self._visible_zones.clear()
         # Loop over each ZoneGroup Element
-        for group_element in tree.findall('ZoneGroup'):
+        for group_element in tree.find('ZoneGroups').findall('ZoneGroup'):
             coordinator_uid = group_element.attrib['Coordinator']
             group_uid = group_element.attrib['ID']
             group_coordinator = None

todo
      1) timeount for lcd display
      2) use rotary encoder to select sonos unit (short term use button to step through)
      3) display volume while volume is being changed
      4) don't change title and artist until track has changed (use soco event class?)
      5) figure out why display is garbling sometimes.  
      6) modify /cleanup rotary encoder class, return ccw or cw, make seperate def for rotary push button
'''

# -------------------------- Main part of program -------------------
# "VCB" represents the entire Volume Control Box, not just the volume knob !
# create all the instances of classes
# most of these  have methods automatically called by switches, etc.
# instance LCD display
LCDDisplay = SonosHW.ExtendedLCD()

# class for all sonos units; methods to change unit with pushbutton
Units = SonosControl.SonosUnits(default="Portable", lcd=LCDDisplay)

# little black button on front of volume control box; used to change sonos unit
SelectUnitButton = SonosHW.PushButton(pin=13,short=.75, callback=Units.select_sonos_unit)

# class for the current track
CurrentTrack = SonosControl.CurrentTrack(units=Units,lcd = LCDDisplay)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VCBPlaystateLED = SonosControl.PlaystateLED(Units, 22, 27, 17)

# class for the sonos volume, methods to change volume, display volume, show the playstate, change playstate
VolumeChanger = SonosControl.SonosVolCtrl(units=Units, lcd=LCDDisplay,
                                                  vol_ctrl_led=VCBPlaystateLED,
                                                  up_increment=4, down_increment=5)
# instance of the rotary encoder + button
# todo make thes into seperate classes, they do diffent things (even though it's one physical device)
VolumeKnob = SonosHW.RotaryEncoder(pinA=19,pinB=26,button=4,callback_func=VolumeChanger.change_volume)

# Something to show on the screen when vol control box starts up
LCDDisplay.display_text("Sonos Volume Control", Units.active_unit.player_name, timeout=5, sleep=5)
time.sleep(5)

while True:
    try:
        # change rotary encoder LED depending on play state
        VCBPlaystateLED.play_state_LED()
        # display what is currently playing, timeout after 60 seconds (to save battery life)
        CurrentTrack.display_track_info(timeout=60)
        # check to see if display is timed out, turn off backlight if it has
        LCDDisplay.check_display_timeout()

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()                      # clean up GPIO on CTRL+C exit
        LCDDisplay.clean_up()               # clean up lcd, turn off backlight

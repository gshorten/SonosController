#!/usr/bin/env python

import SonosHW                  # has the hardware bits - rotary encoder, lcd, etc
import SonosControl             # has classes for controlling the sonos system
import RPi.GPIO as GPIO
import time
import OLEDDisplay

'''
Raspberry pi zero based Sonos music system controller.

See modules SonosHW and SonosControl for class details

https://github.com/gshorten/volcontrol
https://sites.google.com/shortens.ca/sonoswallbox/portable-sonos-volume-control

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
     
      3) display volume while volume is being changed
      4) don't change title and artist until track has changed (use soco event class?)
      5) figure out why display is garbling sometimes. 
        
'''

# instance LCD display
LCDDisplay = OLEDDisplay.OLED()

# All sonos units; methods to change unit with pushbutton
Units = SonosControl.SonosUnits(default_name="Portable", lcd=LCDDisplay)

# class instance for the currently playing track
CurrentTrack = SonosControl.CurrentTrack(units=Units,lcd = LCDDisplay)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VCBPlaystateLED = SonosControl.PlaystateLED(Units, green=6, blue=13, red=5)

# class instance for the volume control; methods to change volume
VCBRotaryControl = SonosControl.SonosVolCtrl(units=Units, lcd=LCDDisplay,
                                             vol_ctrl_led=VCBPlaystateLED, up_increment=4, down_increment=5,)
# instance of the rotary encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=9, pinB=8, rotary_callback=VCBRotaryControl.change_volume)

# instance of the volume control button
VolumeButton = SonosHW.PushButtonShortLong(button_pin=24, callback=VCBRotaryControl.pause_play_skip,
                                  gpio_up_down='down', long_press=1, debounce=25)

# little black button on front of volume control box; used to change sonos unit
SelectUnitButton = SonosHW.SinglePressButton(pin=13, callback=Units.select_unit_single_press, gpio_up=1)

# Something to show on the screen when vol control box starts up
LCDDisplay.display_text("Volume Control", Units.active_unit_name)
time.sleep(3)

while True:
    try:
        # change rotary encoder LED depending on play state
        VCBPlaystateLED.play_state_LED()
        # display what is currently playing, timeout after 60 seconds (to save battery life)
        CurrentTrack.display_track_info()
        # check to see if display is timed out, turn off backlight if it has
        LCDDisplay.check_display_timeout()
        time.sleep(5)

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()                      # clean up GPIO on CTRL+C exit
        LCDDisplay.clean_up()               # clean up lcd, turn off backlight

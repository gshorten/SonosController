#!/usr/bin/env python

import SonosHW                  # has the hardware bits - rotary encoder, display, etc
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
Units = SonosControl.SonosUnits(default_name="Garage", display=LCDDisplay)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VCBPlaystateLED = SonosControl.PlaystateLED(Units, green=6, blue=13, red=5, on="low")

# class instance for the volume control; methods to change volume
VCBRotaryControl = SonosControl.SonosVolCtrl(units=Units, display=LCDDisplay,
                                             vol_ctrl_led=VCBPlaystateLED, up_increment=4, down_increment=5, )
# instance of the rotary encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=9, pinB=8, rotary_callback=VCBRotaryControl.change_volume)

# instance of the volume control button
VolumeButton = SonosHW.PushButtonShortLong(button_pin=12, callback=VCBRotaryControl.pause_play_skip,
                                  gpio_up_down='down', long_press=1, debounce=25)

# little black button on front of volume control box; used to change sonos unit
SelectUnitButton = SonosHW.SinglePressButton(pin=24, callback=Units.select_unit_single_press, gpio_up=1)

# Something to show on the screen when vol control box starts up
LCDDisplay.display_text("Volume Control", Units.active_unit_name)
time.sleep(3)

# Display updater
Updater = SonosControl.SonosDisplayUpdater(Units,LCDDisplay,VCBPlaystateLED)

# get list of sonos units, print list
Units.get_units()



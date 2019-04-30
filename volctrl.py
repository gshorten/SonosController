#!/usr/bin/env python
import SonosHW
import SonosControl
import RPi.GPIO as GPIO
import soco

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
'''

# -------------------------- Main part of program -------------------

# instance LCD display
LCDDisplay = SonosHW.ExtendedLCD()

# little black button on front of volume control box
SelectUnitButton = SonosHW.PushButton(pin=13,callback=SonosControl.SonosUnits.select_sonos_unit)
# make instance of all sonos units
Units = SonosControl.SonosUnits(pushbutton=SelectUnitButton, default="Portable", lcd=LCDDisplay)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VolCtrl_PlaystateLED = SonosControl.PlaystateLED(Units.active_unit, 22, 27, 17)

# create instance of extended LCD for volume control box
VolCtrlLCD = SonosControl.SonoslCtrlDisplay(Units.active_unit, LCDDisplay)

# Volume control instance - changes volume using callback from the rotary encoder.
# is a sublcas of the rotary encoder
PiZeroSonosVolumeCtrl = SonosControl.SonosVolCtrl(pinA=19, pinB=26, button_pin=4,
                                                  callback=SonosControl.SonosVolCtrl.change_volume,
                                                  sonos_unit=Units.active_unit, lcd=LCDDisplay,
                                                  vol_ctrl_lcd=VolCtrlLCD, vol_ctrl_led=VolCtrl_PlaystateLED,
                                                  up_increment=4, down_increment=5)

# Something to show on the screen when vol control box starts up
LCDDisplay.display_text("Sonos Volume Control", Units.active_unit.player_name, timeout=5)

while True:
    try:
        # change LED knob LED depending on play state
        VolCtrl_PlaystateLED.play_state_LED()
        # display what is currently playing
        VolCtrlLCD.display_track_info(timeout=60)
        # display volume (if changed)
        #PiZeroSonosVolumeKnob.display_volume()
        # check to see if display is timed out, turn off backlight if it has
        LCDDisplay.check_display_timeout()

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()                      # clean up GPIO on CTRL+C exit
        LCDDisplay.clean_up()               # clean up lcd, turn off backlight

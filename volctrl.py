#!/usr/bin/env python
import SonosHW
import SonosControl
import RPi.GPIO as GPIO
import soco

# this is morphing into my new OOP based volume control

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

#todo
#       1) timeount for lcd display
#       2) use rotary encoder to select sonos unit (short term use button to step through)
#       3) display volume while volume is being changed
#       4) don't change title and artist until track has changed (use soco event class?)
#       5) see if can use one class for volume control, make it subclass of rotaryencoder - but don't know how to
#           make the callback work...it's calling itself then.


# -------------------------- Main part of program -------------------

# assign sonos player to unit object
#todo use a second rotary control to select sonos units!
# for now it is hard coded :-(
#unit = soco.discovery.by_name("Garage")
unit = soco.discovery.by_name("Kitchen")
print(unit, unit.player_name)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VolCtrl_PlaystateLED = SonosControl.PlaystateLED(unit, 22, 27, 17)

# This changes the volume of the sonos unit
# contains the callback method called by the PiZeroEncoder object
# it's not called directly, but via the callback when the volume knob is turned (or pushed)
PiZeroSonosVolumeKnob = SonosControl.SonosVolCtrl(pinA=19, pinB=26, button_pin=4,
                      callback=SonosControl.SonosVolCtrl.change_volume,sonos_unit=unit,
                      vol_ctrl_led=VolCtrl_PlaystateLED, up_increment=4, down_increment=5)

# create instance of extended LCD for volume control box
VolCtrlLCD = SonosControl.SonoslCtrlDisplay(unit,timeout=15)

#create simple pushbutton on the front panel; triggers callback
TestButton = SonosControl.SelectUnitPushbutton(pin=13,proc_func=SonosControl.SelectUnitPushbutton.test_button)
#VolCtrlEventMonitor = SonosControl.EventMonitor(unit)

unitlist = SonosControl.SonosUnits.get_sonos_units()
while True:
    try:
        # change LED knob LED depending on play state
        VolCtrl_PlaystateLED.play_state_LED()
        # display what is currently playing
        VolCtrlLCD.display_track_info()
        VolCtrlLCD.display_timeout()
        #todo see if we can use soco.events to trigger light change and lcd display of track with callback functions.
        # but probably unecessary as this method is faster than the sonos app on phone :-)
        #VolCtrlEventMonitor.get_events()

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()                      # clean up GPIO on CTRL+C exit
        VolCtrlLCD.clean_up()               # clean up lcd, turn off backlight
        #VolCtrlEventMonitor.unsubcribe_events()
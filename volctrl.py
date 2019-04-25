#!/usr/bin/env python
import RGBRotaryEncoder
import SonosControl
import Rpi.GPIO as GPIO
import soco
import time
import Adafruit_CharLCD as LCD
import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd


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


# -------------------------- Main part of program -------------------

# assign sonos player to unit object
#todo use a second rotary control to select sonos units!
# for now it is hard coded :-(
#unit = soco.discovery.by_name("Garage"
unit = soco.discovery.by_name("Portable")
print(unit, unit.player_name)

# create LED for the volume knob
VolCtrlLED = RGBRotaryEncoder.KnobLED(green=22, red=27, blue=17)

# create play state change LED object
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VolCtrl_PlaystateLED = SonosControl.PlaystateLED(unit,VolCtrlLED)

# This changes the volume of the sonos unit
# contains the callback method called by the PiZeroEncoder object
# it's not called directly, but via the callback when the volume knob is turned (or pushed)
PiZeroSonosVolumeKnob = SonosControl.SonosVolCtrl(unit, VolCtrlLED, up_increment=4, down_increment=5)

# create rotary encoder instance, it decodes the rotary encoder and generates the callbacks for the VolumeKnob
PiZeroEncoder = RGBRotaryEncoder.RotaryEncoder(pinA=19, pinB=26, button=4, callback=PiZeroSonosVolumeKnob.change_volume)

# create LCD display instance
# this makes a two line monochrome adafruit lcd display
#lcd = LCD.Adafruit_CharLCDPlate()
lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

while True:
    try:
        VolCtrl_PlaystateLED.play_state_LED()
        # change LED knob LED depending on play state
        # the volume control triggers methods based on interrupts, changing the colour of the LED has to be polled in
        # in the main program loop

        # display what is currently playing
        currently_playing = SonosControl.TrackInfo(unit)
        SonosControl.DisplayTrackInfo.display_currently_playing(currently_playing, lcd, dur=5)
        #todo see if we can use soco.events to trigger light change with a callback function.
        # but probably unecessary as this method is faster than the sonos app on phone :-)
    except KeyboardInterrupt:
        lcd.clear()
        lcd.set_backlight(0)
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit

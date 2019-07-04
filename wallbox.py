#!/usr/bin/env python

"""
Plays and controls a Sonos music system with inputs from a 1957 Seeburg wallbox.

Has an 2x16 display display, rotary encoder for volume control, rgb led on the rotary control to indicate playstate,
and a pushbutton for selecting the sonos unit to play through.

"""

import SonosControl
import SonosHW
import i2cCharLCD

# LCD on the wallbox
WallboxLCD = i2cCharLCD.ExtendedAdafruitI2CLCD()
# Sonos units
Units = SonosControl.SonosUnits(display=WallboxLCD, default_name='Kitchen')
# Wallbox sonos player
SeeburgWallboxPlayer = SonosControl.WallboxPlayer(units=Units, display=WallboxLCD)
# The Seeburg wallbox
SeeburgWallbox = SonosHW.WallBox(pin=9, callback=SeeburgWallboxPlayer.play_selection)
# Playstate change LED
WallboxPlaystateLED = SonosControl.PlaystateLED(Units, green=6, blue=13, red=5, on="low")
# Display updater
Updater = SonosControl.SonosDisplayUpdater(Units,WallboxLCD,WallboxPlaystateLED)
# Volume Control
WallboxRotaryControl = SonosControl.SonosVolCtrl(units=Units, display=WallboxLCD,
                                                 vol_ctrl_led=WallboxPlaystateLED, up_increment=4, down_increment=5)
# Rotary Encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=11, pinB=7, rotary_callback=WallboxRotaryControl.change_group_volume)
# button on the volume control
VolumeButton = SonosHW.PushButtonShortLong(button_pin=12, callback=WallboxRotaryControl.pause_play_skip,
                                  gpio_up_down='down', long_press=1, debounce=50)

# Button groups or ungroups units from the active unit group (set with default parameter in units class)
GroupUnitsButton = SonosHW.PushButtonShortLong(button_pin=18,callback=Units.group_units,long_press=1,
                                               gpio_up_down = "up", debounce=100)

# Something to show on the screen when vol control box starts up
print('active unit: :', Units.active_unit_name)
WallboxLCD.display_text("Wallbox On", Units.active_unit_name, sleep=3)

# get list of sonos units, print list
Units.get_units()


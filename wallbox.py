#!/usr/bin/env python3

"""
Plays and controls a Sonos music system with inputs from a 1957 Seeburg wallbox.

Has an 2x16 OLED display, rotary encoder for volume control, rgb playstate_led on the rotary control to indicate playstate,
and a pushbutton for selecting the pageset that is loaded on the wallbox - ie, the selections that can be played.
It's completely event driven, except for some loops that
run in separate threads that listen for changes on the currently selected sonos unit.

When nothing is playing on the Sonos and the display is timed out the display shows the current and forecast weather.
"""

from SonosControl import *
from SonosHW import *
import OLED128X64
from Weather import UpdateWeather

# weather updater
WeatherUpdater = UpdateWeather(update_freq=10)
# LCD on the wallbox
WallboxLCD = OLED128X64.OLED(WeatherUpdater, showing_weather=False, char_width=24, pixels_high=64)
# Sonos units
Units = SonosUnits(display=WallboxLCD, default_name='Kitchen')
#on start up trigger rfid read of loaded page manually
# Wallbox sonos player
SeeburgWallboxPlayer = WallboxPlayer(units=Units, display=WallboxLCD)
# The Seeburg wallbox
SeeburgWallbox = SonosHW.WallBox(pin=9, callback=SeeburgWallboxPlayer.play_selection)
# Playstate change LED
WallboxPlaystateLED = PlaystateLED(Units, green=6, blue=13, red=5, on="low")
# Display updater
Updater = SonosDisplayUpdater(Units, WallboxLCD, WallboxPlaystateLED, WeatherUpdater)
# Volume Control
WallboxRotaryControl = SonosVolCtrl(units=Units, updater=Updater, display=WallboxLCD,
                                                 vol_ctrl_led=WallboxPlaystateLED, weather=WeatherUpdater,
                                                 up_increment=4, down_increment=5)
# Rotary Encoder (for the volume control)
VolumeKnob = RotaryEncoder(pinA=11, pinB=7, rotary_callback=WallboxRotaryControl.change_volume)
# button on the volume control
PausePlayButton = TimedButtonPress(pin=12, callback=WallboxRotaryControl.pause_play_skip, long_press_sec=1)
# Button that manually selects wallbox pages
SelectPageSetButton = ButtonPress(pin = 18,callback = SeeburgWallboxPlayer.select_wallbox_pageset)
# display time out loop
OLEDTimeOut = DisplayTimeOut(WallboxLCD,Updater,timeout=5)
# RFID reader that gets the page tag number and switches the wallbox page set
PageReader = RFIDReader(callback = SeeburgWallboxPlayer.get_wallbox_tracks, port = "/dev/ttyUSB0")

# Something to show on the screen when vol control box starts up
print('active unit: :', Units.active_unit_name)
# get list of sonos units, print list to console
Units.get_units()


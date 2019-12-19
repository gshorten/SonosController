#!/usr/bin/env python

"""
Plays and controls a Sonos music system with inputs from a 1957 Seeburg wallbox.

Has an 2x16 display display, rotary encoder for volume control, rgb playstate_led on the rotary control to indicate playstate,
and a pushbutton for selecting the sonos unit to play through.  It's completely event driven, except for some loops that
run in separate threads that listen for changes on the currently selected sonos unit.

When nothing is playing on the Sonos and the display is timed out the display shows the current and forecast weather.

"""

import SonosControl
import SonosHW
import SonosUtils
# import i2cCharLCD
import OLED128X64
import Weather


# weather updater
WeatherUpdater = Weather.UpdateWeather(update_freq=10)
# LCD on the wallbox
WallboxLCD = OLED128X64.OLED(WeatherUpdater, showing_weather=False, char_width=24, pixels_high=64)
# Sonos units
Units = SonosControl.SonosUnits(display=WallboxLCD, default_name='Kitchen')
#on start up trigger rfid read of loaded page manually

SeeburgWallboxPlayer = SonosControl.WallboxPlayer(units=Units, display=WallboxLCD)
# The Seeburg wallbox
SeeburgWallbox = SonosHW.WallBox(pin=9, callback=SeeburgWallboxPlayer.play_selection)
# Playstate change LED
PagesSwitcher = SonosHW.WallboxPagesSwitch(switch_pin=21,callback =SeeburgWallboxPlayer.get_wallbox_tracks)
# Wallbox sonos player

WallboxPlaystateLED = SonosControl.PlaystateLED(Units, green=6, blue=13, red=5, on="low")
# Display updater
Updater = SonosControl.SonosDisplayUpdater(Units, WallboxLCD, WallboxPlaystateLED, WeatherUpdater)
# Volume Control
WallboxRotaryControl = SonosControl.SonosVolCtrl(units=Units, updater=Updater, display=WallboxLCD,
                                                 vol_ctrl_led=WallboxPlaystateLED, weather=WeatherUpdater, up_increment=4, down_increment=5)
# Rotary Encoder (for the volume control)
VolumeKnob = SonosHW.RotaryEncoder(pinA=11, pinB=7, rotary_callback=WallboxRotaryControl.change_volume)
# button on the volume control
VolumeButton = SonosHW.PushButtonShortLong(button_pin=12, callback=WallboxRotaryControl.pause_play_skip,
                                  gpio_up_down='down', long_press=1, debounce=50)

# Button groups or ungroups units from the active unit group (set with default parameter in units class)
GroupUnitsButton = SonosHW.PushButtonShortLong(button_pin=18,callback=Units.group_units,long_press=1,
                                               gpio_up_down = "up", debounce=100)
# display time out
OLEDTimeOut = SonosControl.DisplayTimeOut(WallboxLCD,Updater,timeout=5)
# limit switch in wallbox that triggers the rfid reader

#get the currently loaded wallbox page set
#PagesSwitcher.read_page_rfid()
SeeburgWallboxPlayer.get_wallbox_tracks(page = "0001")
# Something to show on the screen when vol control box starts up
print('active unit: :', Units.active_unit_name)
# WallboxLCD.display_text("Wallbox On", Units.active_unit_name, sleep=3)

# get list of sonos units, print list
Units.get_units()


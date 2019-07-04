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
      
'''

# instance LCD display
Display = OLEDDisplay.OLED()

# All sonos units; methods to change unit with pushbutton
Units = SonosControl.SonosUnits(default_name="Garage", display=Display)

# create play state change LED object and playstate control
# it changes the colour of the VolCtrlLED based on if the sonos is paused or playing
VCBPlaystateLED = SonosControl.PlaystateLED(Units, green=6, blue=13, red=5, on="low")

# class instance for the volume control; methods to change volume
VCBRotaryControl = SonosControl.SonosVolCtrl(units=Units, display=Display,
                                             vol_ctrl_led=VCBPlaystateLED, up_increment=4, down_increment=5, )
# instance of the rotary encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=9, pinB=8, rotary_callback=VCBRotaryControl.change_volume)

# instance of the volume control button
VolumeButton = SonosHW.PushButtonShortLong(button_pin=12, callback=VCBRotaryControl.pause_play_skip,
                                  gpio_up_down='down', long_press=1, debounce=25)

# little black button on front of volume control box; used to change sonos unit
SelectUnitButton = SonosHW.SinglePressButton(pin=24, callback=Units.select_unit_single_press, gpio_up=1)

# Something to show on the screen when vol control box starts up
Display.display_text("Volume Control", Units.active_unit_name, sleep=3)

# Display updater
Updater = SonosControl.SonosDisplayUpdater(Units, Display, VCBPlaystateLED)

# get list of sonos units, print list
Units.get_units()



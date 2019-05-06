#!/usr/bin/env python

import time
import SonosControl
import SonosHW
import RPi.GPIO as GPIO
import i2cCharLCD
import board
import busio
from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C

"""
Plays and controls a Sonos music system with inputs from a 1957 Seeburg wallbox.

Has an 2x16 lcd display, rotary encoder for volume control, rgb led on the rotary control to indicate playstate,
and a pushbutton for selecting the sonos unit to play through
"""
# adfruit lcd
lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
lcd = Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

# Wallbox LCD display
WallboxLCD = i2cCharLCD.ExtendedAdafruitI2LCD(lcd)

WallboxLCD.display_text("Starting up", "program")

# Sonos units
Units = SonosControl.SonosUnits(default_unit="Portable", lcd=WallboxLCD)

# class instance for the currently playing track
CurrentTrack = SonosControl.CurrentTrack(units=Units,lcd = WallboxLCD)

# Wallbox sonos player
SeeburgWallboxPlayer = SonosControl.WallboxPlayer(units=Units, lcd=WallboxLCD)

# The Seeburg wallbox
SeeburgWallbox = SonosHW.WallBox(pin=12, callback=SeeburgWallboxPlayer.play_selection)

# Playstate change LED
WallboxPlaystateLED = SonosControl.PlaystateLED(Units, 27, 17, 18)

# Volume Control
WallboxRotaryControl = SonosControl.SonosVolCtrl(units=Units, lcd=WallboxLCD,
                                                 vol_ctrl_led=WallboxPlaystateLED, up_increment=4, down_increment=5)
# Rotary Encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=19, pinB=21, rotary_callback=SonosControl.SonosVolCtrl)

# instance of the volume control button
VolumeButton = SonosHW.PushButton(button_pin=25, callback=WallboxRotaryControl.pause_play_skip,
                                  gpio_up_down='down', short=.75, debounce=25)

# little black button on front of volume control box; used to change sonos unit
SelectUnitButton = SonosHW.PushButton(button_pin=16, short=.75, callback=Units.select_sonos_unit, gpio_up_down='up')

# Something to show on the screen when vol control box starts up
print('active unit: :', Units.active_unit_name)
WallboxLCD.display_text("Wallbox Controller", Units.active_unit.player_name, timeout=5, sleep=1)
time.sleep(3)

while True:
    try:
        # change rotary encoder LED depending on play state
        WallboxPlaystateLED.play_state_LED()
        # display what is currently playing, timeout after 60 seconds (to save battery life)
        CurrentTrack.display_track_info(timeout=60)
        # check to see if display is timed out, turn off backlight if it has
        WallboxLCD.check_display_timeout()

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()                      # clean up GPIO on CTRL+C exit
        WallboxLCD.clean_up()               # clean up lcd, turn off backlight
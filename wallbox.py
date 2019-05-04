
import time
import SonosControl
import SonosHW

"""
Plays and controls a Sonos music system with inputs from a 1957 Seeburg wallbox.

Has an 2x16 lcd display, rotary encoder for volume control, rgb led on the rotary control to indicate playstate,
and a pushbutton for selecting the sonos unit to play through
"""

# Wallbox LCD display
WallboxLCD = SonosHW.ExtendedAdafruitI2LCD()

# Sonos units
Units = SonosControl.SonosUnits(default_unit="Portable", lcd=WallboxLCD)

# class instance for the currently playing track
CurrentTrack = SonosControl.CurrentTrack(units=Units,lcd = WallboxLCD)

# Wallbox sonos player
SeeburgWallboxPlayer = SonosControl.WallboxPlayer(units=Units, lcd=WallboxLCD)

# The Seeburg wallbox
SeeburgWallbox = SonosHW.WallBox(callback=SeeburgWallboxPlayer.play_selection)

# Playstate change LED
WallboxPlaystateLED = SonosControl.PlaystateLED(Units, 22, 27, 17)

# Volume Control
WallboxRotaryControl = SonosControl.SonosVolCtrl(units=Units, lcd=WallboxLCD,
                                                 vol_ctrl_led=WallboxPlaystateLED, up_increment=4, down_increment=5)
# Rotary Encoder
VolumeKnob = SonosHW.RotaryEncoder(pinA=19, pinB=26, rotary_callback=SonosControl.SonosVolCtrl)
# Sonos Controller(s)
Sonos volume control box, 
Seeburg wallbox sonos controller

Main programs:  wallbox.py - uses Seeburg wallbox to play selections on Sonos music system
                volctrl.py - portable sonos controller
Modules:        SonosHW    - generic input devices for raspberry pi; push buttons, rotary encoders, Seeburg wallbox           
                i2cCharLCD - subclass of the adafruit character lcd, has methods for centering, displaying text
                SonosControl - has methods for controlling the sonos system with the devices in SonosHW; pausing, playing tracks,
                               displaying information, changing volume, playing favorites and radio stations, etc.

It's a program used to control a sonos system with a raspberry pi.  I have two implentations, a portable volume controller / track display, and a 1957 Seeburg jukebox wallbox which controls my sonos system via the jukebox pushbuttons.
The volume control box has a battery, power supply, custom interface board, rgb rotary encoder w/ switch, and momentary pushbutton.

Volume Controller (volctrl.py)
Uses a pi zero, which sits in a little box, with volume control, change unit button, and 2 line lcd display
Functions:
  -shows current track
  -rotary encoder changes volume
  -rgb led on encoder shows playstate of selected sonos unit (green = playing, red = paused, blue =  transitioning)
  -rotary encoder  short button press pauses / plays sonos unit
  -rotary encoder long button press skips to next track
  -second pushbutton is used to switch the sonos unit being controlled
  
It uses the SoCo.soco module https://github.com/SoCo/SoCo

The wallbox controller (wallbox.py) takes button presses from the 1957 seeburg wallbox and plays radio stations, playlists, and tracks on the sonos system.  It uses a raspberry pi and same components as the volume controller, but additionally has a custom interface board to translate the 24v ac pulses from the wallbox to 3.3v logic signals for the pi.  The code for both projects is 90% common, with just the classes to translate the wallbox pulses into a number 0-199, and then to play the corresponding selection on the sonos being specific to wallbox.py.

See my project page at https://sites.google.com/shortens.ca/sonoswallbox/home  (this also has stuff on the volume control)

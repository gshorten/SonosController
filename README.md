# volcontrol
Sonos volume control box

It's a program used to control a sonos system with a raspberry pi zero.

The pi sits in a little box, with volume control, change unit button, and 2 line lcd display
Functions:
  -shows current track
  -rotary encoder changes volume
  -rgb led on encoder shows playstate of selected sonos unit (green = playing, red = paused, blue =  transitioning)
  -rotary encoder  short button press pauses / plays sonos unit
  -rotary encoder long button press skips to next track
  -second pushbutton is used to switch the sonos unit being controlled
  
It uses the SoCo.soco module https://github.com/SoCo/SoCo
  
The volume control box has a battery, power supply, custom interface board, rgb rotary encoder w/ switch, and momentary pushbutton.

Related project is using a 1957 seeburg wallbox to control a sonos system 
See my project page at https://sites.google.com/shortens.ca/sonoswallbox/home  (this also has stuff on the volume control)

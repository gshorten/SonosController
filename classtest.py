
import RGBRotaryEncoder as Encoder
import RPi.GPIO as GPIO
import soco

class SonosVolCtrl:

    def __init__(self,unit):
        # sonos unit
        self.unit = unit


    def change_volume(self,event):
        # callback function to change the volume of the sonos unit
        # is called from the VolControl object
        new_volume = 0
        # get the volume of the sonos unit
        unit_volume = self.unit.volume
        # increment the volume up or down based on event value
        # can be 1 or 2
        # also limit volume to between 0 and 100
        if event == 1:
            # direction is clockwise
            new_volume = unit_volume + 4
            if new_volume > 100:
                new_volume = 100
            self.unit.volume = new_volume
        elif event == 2:
            # direction is counter clockwise, volume down
            # turn volume down more quickly than up, better for the user!
            new_volume = unit_volume - 5
            if new_volume < 0:
                new_volume = 0
            self.unit.volume = new_volume
        print ("new volume: ", new_volume)


# assign sonos player to unit object
unit = soco.SoCo('192.168.0.21')        # portable
# create volume control knob
VolumeKnob = SonosVolCtrl(unit)
RotaryVol = Encoder.RotaryEncoder(19, 26, 4, VolumeKnob.change_volume(event))

while True:
    try:
       pass
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
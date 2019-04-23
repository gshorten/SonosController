
import RGBRotaryEncoder as Encoder
import RPi.GPIO as GPIO
import soco

class SonosVolCtrl:
    # processes the callback from the rotary encoder to change the volume of the sonos unit

    def __init__(self, sonos_unit, up_increment = 4, down_increment = 5):
        # sonos unit
        self.unit = sonos_unit
        self.upinc = up_increment   # how much to change the volume each click of the volume knob
        self.downinc = down_increment   #how much to change the volume down

    def change_volume(self,event):
        # callback function to change the volume of the sonos unit
        # is called from the RotaryEncoder class
        # event is returned from the RotaryEncoder class, can be either 1(clockwise rotation) or 2 (counter cw)
        new_volume = 0
        # get the volume of the sonos unit
        unit_volume = self.unit.volume
        # increment the volume up or down based on event value
        # also limit volume to between 0 and 100
        if event == 1:
            # direction is clockwise
            new_volume = unit_volume + self.upinc
            if new_volume > 100:
                new_volume = 100
            self.unit.volume = new_volume
        elif event == 2:
            # direction is counter clockwise, volume down
            # turn volume down more quickly than up, better for the user!
            new_volume = unit_volume - self.downinc
            if new_volume < 0:
                new_volume = 0
            self.unit.volume = new_volume
        print ("new volume: ", new_volume)


# assign sonos player to unit object
unit = soco.SoCo('192.168.0.21')        # portable
# create sonos volume control knob instance
VolumeKnob = SonosVolCtrl(unit,4,5)
# create rotary encoder instance
RotaryVol = Encoder.RotaryEncoder(19, 26, 4, VolumeKnob.change_volume)

while True:
    try:
       pass
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
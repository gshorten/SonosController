import soco
import RPi.GPIO as GPIO

class VolumeControl:
    # class for the volume control rotary encoder
    # it's not perfect but works ok
    # have to come up with a better algorithm.
    counter = 0
    def __init__(self, enc_a, enc_b, s_unit, vol_increment=3):
        # s_unit is the sonos unit we are controlling
        self.unit = s_unit
        # initialize variable to store old values for the encoder
        self.old_encoder_values = "11"
        # assign the GPIO pins to variables
        # enc_a is gpio 19, enc_b is gpio 26
        self.enc_a = enc_a
        self.enc_b = enc_b
        self.debounce = 1            # we only need minimal debounce
        self.vol_increment = vol_increment
        # amount to increment volume by.  2 - 3 seems a good value to use
        GPIO.setmode(GPIO.BCM)
        # define the Encoder switch inputs
        GPIO.setup(self.enc_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.enc_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # set up the callback function
        GPIO.add_event_detect(self.enc_a, GPIO.BOTH, callback=self.set_volume, bouncetime=self.debounce)
        GPIO.add_event_detect(self.enc_b, GPIO.BOTH, callback=self.set_volume, bouncetime=self.debounce)
        # the rotary encoder has two channels, but seems to work best if we just use one channel to trigger the callback
        # function in the volume_set class.
        # falling seems to work best as encoder outputs are normally high, they go low

    def set_volume(self,channel):
        # -------------------------------------------------------------------------------------------------------------
        # | function gets the outputs from the rotary encoder and changes the volume of the sonos unit                 |
        # | encoder puts out a 1 or 0 for each channel at each detent as it is rotated   (2 bit gray code)             |
        # | adding the previous two outputs to the latest makes a string of 4 0s and 1s                                |
        # | not a binary number but we can use it to tell if knob was turned clockwise (cw) or counter clockwise (ccw) |
        # | certain strings only come up if direction is ccw or cw, some strings are common to both                    |
        # -------------------------------------------------------------------------------------------------------------
        try:
            # store the output of both channels from the rotary encoder
            encoder_a, encoder_b = GPIO.input(self.enc_a), GPIO.input(self.enc_b)
            two_bit_code = str(encoder_a) + str(encoder_b)
            print ("turn no:", self.counter,"bits:",two_bit_code)
            self.counter += 1
            # if channel == self.enc_a:
            #     new_encoder_values = str(encoder_a) + str(encoder_b)
            # elif channel == self.enc_b:
            #     new_encoder_values = str(encoder_b) + str(encoder_a)
            # unit_volume = self.unit.volume
            # combine the value of encoder_a and encoder_b (both either 0 or 1) to get a two digit string

            # combine the old value and the new value to get a 4 digit binary string, convert to a decimal
            #   number to make values more human readable
            # encoder_value = int(new_encoder_values + self.old_encoder_values,2)
            # print ("channel :",channel, "new encoder value : ",new_encoder_values)
            # print ("encoder value decimal: ",encoder_value)  # for debugging
            # if encoder_value in (10,11,14):
            #     # if we get one of these numbers direction is counter clockwise, volume down
            #     # occasionally we'll get one of the numbers for direction up, but not that often
            #     # other numbers (like 15, which comes up in both directions) are ignored.
            #     new_volume = unit_volume - self.vol_increment
            #     if new_volume < 0 :
            #         # don't try to make volume less than 0
            #         new_volume = 0
            #     self.unit.volume = new_volume
            #     print ("Volume went down, is now:", new_volume)  # for debugging
            # elif encoder_value in (3,7,12,13) :
            #     # direction is clockwise, volume up
            #     new_volume = unit_volume + self.vol_increment
            #     if new_volume > 100 :
            #         new_volume = 100
            #         # don't try to make volume more than 100
            #     self.unit.volume = new_volume
            #     print ("Volume went up, is now:", new_volume)
            # # save the current encoder value so we can add it to the next one
            self.old_encoder_values = new_encoder_values
        except:
            return

unit = soco.SoCo('192.168.0.21')        # portable
unit_volume_set = VolumeControl(19,26,unit,3)
while True:
    try:
       pass
    except KeyboardInterrupt:
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
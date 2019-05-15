
"""
Tests wallbox decode algorithm
"""

import RPi.GPIO as GPIO
import time

class WallBox:
    """
    Interface to the Seeburg WA-200 Jukebox wallbox.  Decodes the output of the wallbox into a number 0 - 199

    The Seeburg wallbox makes a selection with a combination of a letter press (A - V, excluding I, O, as these
    could be confused with numbers 1 and 0), for a total of 20 letters, and one of 10 numbers (1- 9,0).  The two
    combined totals 200 possible selections.

    The output from the wallbox is 24v ac pulses, 4-5 ac cycles per pulse.  These signals are sent to a Fairchild
    MID 400 AC line sensing chip which converts them to a 5v logic signal.   The signal from the chip is +5v, when it
    sees 24v ac it pulls the output to ground and latches until the ac signal has stopped.  Perfect square waves.  The
    5v is dropped to 3.3v with a voltage divider.

    The processed signal from the wallbox looks like this:
                                                                                                |
    +5v --------|          |---------|                        |----------|         |------------|-----------
                |          |         |                        |          |         |            |
                |          |         |                        |          |         |            |
                |          |         |                        |          |         |        occasional noise
    0v          -----------          -------------------------           -----------
                ^  ~42ms   ^  ~36ms  ^        ~220ms          ^
                ^ ~78ms edge to edge ^     ~260 - 270 ms edge to edge    ^

                ^ start letters      ^     gap between        ^start numbers               finished - no more edges
                                         letters & numbers

    Sometimes we get a noise spike about 500ms after the last pulse,
    it is very short - 1-2 ms, so we have to remove this in software, as the pi will read it.

    Definitions:
        - pulse beginning:      the start of a pulse, falling from 3.3v to 0
        - pulse:                a single pulse from falling edge to next falling edge

    Methods:
        - pulse_count           Threaded callback when buttons are pressed on the wallbox. Counts the letters and
                                numbers pressed
        - wait_for_pulses_end   loops waiting for last pulse from wallbox.
        - convert_wb            converts the letter and number selection into a number 0- 199
    """

    # constants for detecting and decoding wallbox pulses
    LETTER_MAX = .275       # minimum and maximum gap between letters and numbers
    LETTER_MIN = .260
    PULSE_MAX = .085        # maximum duration of a letter or number pulse
    PULSE_MIN = .070        # minimum duration of a letter or number pulse
    DEBOUNCE = 20           # don't need a big debounce - maybe not at all, signal is clean
    END_GAP = .350          # time to wait after last pulse - we assume pulses have stopped.

    def __init__(self, pin, callback):
        """
        :param pin:         GPIO pin for the wallbox input.
        :type pin:          int
        :param callback:    name of the method that does something with the wallbox pulses
        :type callback:     object (method name)
        """
        self.pin = pin                      # used to be gpio 20, will change
        self.callback = callback
        self.first_pulse = True
        self.last_pulse_start = 0
        self.counting_numbers = False
        self.letter_count = 0
        self.number_count = 0
        self.pulses_started = False
        self.last_pulse_start = 0
        self.pulses_ended = False
        self.counting_pulses = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.IN)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self.pulse_count, bouncetime=self.DEBOUNCE)
        # GPIO pin has +3 volts on it, the Fairchild MID 400 AC line sensing chip pulls this to ground
        # when a wallbox pulse starts, so we want to trigger the callback on the falling edge.

    def pulse_count(self,cb):
        """
        Counts the pulses from the wallbox, first the letters, then the numbers.  Filters out stuff that is not a
        valid pulse.
        """
        # get the time the pulse started
        self.pulse_start_time = time.time()
        # calculate the duration from the last pulse
        duration = time.time() - self.last_pulse_start
        # print("Duration is: ", round(duration, 3))

        # next check to see if it is a valid pulse, ie not noise, or the very long pulse between sets of pulses
        # if either a regular pulse or the gap between letters and numbers then start (or continue) counting
        # this filters out any short duration noise spikes, which usually occur after pulses are finished.
        if self.LETTER_MAX > duration > self.LETTER_MIN or self.PULSE_MAX > duration > self.PULSE_MIN:
            # print('valid pulse')
            # if it's not the first pulse then start counting
            if not self.first_pulse:
                #check for gap between the letters and numbers
                if self.LETTER_MAX > duration > self.LETTER_MIN:
                    #if it matches the letter-number gap flag that we are now counting numbers, not letters
                    self.counting_numbers = True
                    print('================Now counting numbers ====================')
                else:
                    if not self.counting_numbers:
                        # we are counting letters
                        self.letter_count += 1
                        print('Letter count: ', str(self.letter_count))
                    else:
                        self.number_count += 1
                        print('Number count: ', str(self.number_count))

            elif self.first_pulse:
                # if it is the first pulse then don't count it yet, just record the time of the pulse,
                print('******************* PULSES STARTED ***********************')
                # reset first pulse flag
                self.first_pulse = False
                self.counting_pulses = True

        # record the time of this pulse
        self.last_pulse_start = time.time()
        return

    def wait_for_pulses_end(self):
        """
        Called when wallbox pulses start.  Starts a while loop, times each pulse,
        if there is no pulse 750ms after the last one then assume that the whole train of pulses has ended, call the
        function that plays the wallbox selection

        Also reset class counters and flags for next train of pulses.
        """
        # Loop until there is no pulse for a length of time longer than the longest pulse, which is the letter number
        # gap in the pulses.  use the pulses_ended flag
        while self.counting_pulses:
            # print('started waiting for end')
            # print('letter count:', self.letter_count)
            # print('number count:', self.number_count)
            # check to see how long it's been since the last pulse started
            gap = time.time() - self.last_pulse_start
            if gap > self.END_GAP:
                print('Pulses have ended')
                # then pulses have ended, stop looping, reset all counters, convert letters and numbers, and call
                # function to process result
                print ('letter: ', self.letter_count, 'number: ', self.number_count)
                # get selection number from letters and numbers count
                wbnumber = self.convert_wb(self.letter_count, self.number_count)
                print("wallbox nummber: ", wbnumber)
                # call processing function
                self.callback(self,wbnumber)
                # reset counters and flags
                self.first_pulse = True
                self.letter_count = 0
                self.number_count = 0
                self.counting_pulses = False
                self.counting_numbers = False

            # sleep a little so as to not tie up processor
            time.sleep(.05)


    def test_output(self, wbnumber):
        print("WB sequence finished, selection is:", wbnumber)

    def convert_wb(self,letter, number):
        """
        Turns letter and number into a single number 0-199.

        :param letter:      Number representing the letter pressed on the wallbox (0- 19)
        :type letter:       int
        :param number:      Number representing the number key pressed on the wallbox (0-9)
        :type number:       int
        """

        #  Adjust the letter and number count to get the right tracks
        #         because we look these up by index, python indexes start at 0, so we subtract 1 from letter count
        #
        letter -= 1
        number = (number) * 20
        # it's a base 20 system; with the letters being numbers 0-19, then the number being the "20"'s digit
        # so we have to multply the number by 20 then add it to the letter
        # we add 1 to the number because with this algorithm the last pulse is not counted
        conversion = letter + number +1
        print("Conversion is: ", conversion)
        return conversion


TestWB = WallBox(pin=9, callback= WallBox.test_output)

while True:
    try:
        TestWB.wait_for_pulses_end()
        time.sleep(.1)

    except KeyboardInterrupt:
        # do some cleanup on devices, etc
        GPIO.cleanup()
#!/usr/bin/env python

# Module with generic classes for controlling sonos system with raspberry pi + rotary encoders, switches, lcd displays, etc
# adds sonos specific methods to SonoHW.py

import soco
import time
import SonosHW
from queue import Empty
from Adafruit_CharLCD import Adafruit_CharLCDPlate as LCD
import RPi.GPIO as GPIO


class SonosVolCtrl(SonosHW.RotaryEncoder):
    # processes the callback from the rotary encoder to change the volume of the sonos unit
    # and does stuff when the encoder button is pressed (also via callbacks)

    def __init__(self,pinA, pinB, button_pin, callback, sonos_unit, lcd, vol_ctrl_led, up_increment = 4, down_increment = 5,):
        SonosHW.RotaryEncoder.__init__(self, pinA, pinB, button_pin, callback)
        self.lcd = lcd
        # sonos unit
        self.unit = sonos_unit
        self.upinc = up_increment       # how much to change the volume each click of the volume knob
        self.downinc = down_increment   # how much to change the volume down
        self.vol_ctrl_led = vol_ctrl_led
        self.new_volume = 0
        self.volume_changed_time = 0

    def change_volume(self, event):
        # callback function to change the volume of the sonos unit
        # is called from the RotaryEncoder class
        # event is returned from the RotaryEncoder class, can be either 1(clockwise rotation) or 2 (counter cw)
        new_volume = 0
        # get the volume of the sonos unit
        unit_volume = self.unit.volume
        # increment the volume up or down based on event value
        # also limit volume to between 0 and 100
        if event == 1 or event == 2:
            volume_changed = True
            self.volume_changed_time = time.time()

        if volume_changed:
            if event == 1:
                # direction is clockwise
                self.new_volume = unit_volume + self.upinc
                if self.new_volume > 100:
                    self.new_volume = 100
            elif event == 2:
                # direction is counter clockwise, volume down
                # turn volume down more quickly than up, better for the user!
                self.new_volumenew_volume = unit_volume - self.downinc
                if self.new_volume < 0:
                    self.new_volume = 0
            self.unit.volume = self.new_volume
            print ("new volume: ", self.new_volume)

        elif event == 3 or event ==4:
            # these events are the rotary encoder button being pressed.
            # 3 is down, 4 is up
            # use a seperate def to figure out short or long press.
            if SonosHW.RotaryEncoder.get_button_press_duration(self, event) == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif SonosHW.RotaryEncoder.get_button_press_duration(self, event) == "long":
                try:
                    # long button press, skip to the next track
                    self.vol_ctrl_led.knob_led('off')
                    self.vol_ctrl_led.knob_led('on', 'blue')
                    print("Skipping to next track")
                    self.unit.next()

                except:
                    print("cannot go to next track with this source")

    def display_volume(self):
        time_since_last_vol_change = time.time() - self.volume_changed_time
        if time_since_last_vol_change > 1 and time_since_last_vol_change < 5:
            print('should be displaying the volume')
            self.lcd.display_text('volume is: ', str(self.new_volume), duration=3)

    def pause_play(self):
        # pauses or plays the sonos unit, toggles between the two.
        play_state = self.unit.get_current_transport_info()['current_transport_state']
        print(play_state)
        if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
            self.unit.play()
            print("Now Playing")
        elif play_state == "PLAYING":
            # unit is playing, stop it
            self.unit.pause()
            print("Now Paused")


class PlaystateLED(SonosHW.KnobLED):
    # class to change the sonos volume rotary controller's LED depending on play_state and other things
    # but right now only can think of playstate
    # made it a class in case I think of other unit related things to show on the knob, like is unit in the current
    # group?
    # btw it is a subclass

    def __init__(self, unit, green, red, blue):

        self.unit = unit            #sonos unit we are checking for
        SonosHW.KnobLED.__init__(self, green, red, blue)

    def play_state_LED(self):
        # changes colour of light on encoder button depending on play state of the sonos unit
        unit_state = self.unit.get_current_transport_info()
        # time.sleep(.05)  # pause long enough for sonos to respond
        # todo play with this, we might not need it
        # determine if the sonos unit is playing or not
        play_state = unit_state['current_transport_state']
        if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
            # change the colour of the led
            # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
            self.knob_led('off', 'green')
            self.knob_led('on', 'red')
        elif play_state == "PLAYING":
            self.knob_led('off', 'red')
            self.knob_led('on', 'green')

        return


class SonoslCtrlDisplay():
    # extends ExtendedLCD to add sonos specific methods such as displaying current track info, volume, sonos unit.

    def __init__(self, unit, lcd, duration = 10):
        self.lcd = lcd
        self.unit = unit
        # dictionary to store track information
        self.currently_playing = {'title': "", 'from': "", 'meta': ''}
        self.display_start_time = 0
        self.duration = duration
        self.old_title=""
        self.current_title = ""

    def track_info(self):
        # returns a dictionary "currently_playing" with "title" and "from"
        #   (ie, station, artist) for the currently playing track
        # this is used to update the display, such as after adding a track to the queue or pausing / playing
        # get current track info for the sonos unit.
        # time.sleep(.1)  # pause long enough to get track info, probably don't need this
        #todo make a class for track info?  extend the soco class to add this enhanced info functionality?
        #   also check to see if we can simplify, do we need the siriusxm stuff?
        try:
            self.current_track = self.unit.get_current_track_info()
            if self.is_siriusxm(self.current_track):
                # check to see if it is a siriusxm source,
                #   if so, then get title and artist using siriusxm_track_info function
                current = self.siriusxm_track_info(self.current_track)
                self.currently_playing['title'] = current['xm_title']
                self.currently_playing['from'] = current['xm_artist']

            else:
                self.currently_playing['title'] = self.current_track['title']
                self.currently_playing['from'] = self.current_track['artist']

            if self.currently_playing['title'] == self.currently_playing['from']:  # if title and from are same just display title
                self.currently_playing['from'] = "                "

            if len(self.currently_playing['title']) > 40:
                self.currently_playing['title'] = 'getting title'
                self.currently_playing['from'] = 'getting from'

            self.currently_playing['meta'] = self.current_track['metadata']
            # meta data is  used in main loop to check if the track has changed

        except:
            self.currently_playing['title'] = 'No Title :-('
            self.currently_playing['from'] = 'No Artist :-('
            self.currently_playing['meta'] = ''
        return self.currently_playing

    def display_track_info(self, duration = 10):
        # displays the current track info, unless it has not changed.
        self.current_track = self.track_info()
        self.current_title = self.current_track['title']
        # print('current title: ', self.current_title,'old title: ',self.old_title)
        #self.display_text(self.current_track['title'], self.current_track['from'], self.duration)
        if self.current_title == self.old_title:
            time.sleep(2)
            return
        else:
            #self.set_backlight
            print('track has changed')
            print(self.current_track['title'],"   ",self.current_track['from'])
            self.lcd.display_text(self.current_track['title'], self.current_track['from'], duration)
            time.sleep(1)
            self.old_title = self.current_title



    def is_siriusxm(self, current_track):
        # tests to see if the current track is a siriusxm station
        s_title = current_track['title']
        s_title = s_title[0:7]

        if s_title == 'x-sonos':
            # only siriusxm stations seem to start this way
            return True
        else:
            return False

    def siriusxm_track_info(self,current_track):
        try:
            # gets the title and artist for a sirius_xm track
            track_info = {"xm_title": "", 'xm_artist': ''}
            # title and artist stored in track-info dictionary
            meta = current_track['metadata']
            title_index = meta.find('TITLE') + 6
            title_end = meta.find('ARTIST') - 1
            title = meta[title_index:title_end]
            artist_index = meta.find('ARTIST') + 7
            artist_end = meta.find('ALBUM') - 1
            artist = meta[artist_index:artist_end]

            if title[
               0:9] == 'device.asp':  # some radio stations first report this as title, filter it out until title appears
                track_info['xm_title'] = "    "
                track_info['xm_artist'] = "   "
            else:
                track_info['xm_title'] = title
                track_info['xm_artist'] = artist
        except:
            track_info['xm_title'] = "no title"
            track_info['xm_artist'] = "no artist"
        return track_info


class SelectUnitPushbutton(SonosHW.PushButton):
    # little black pushbutton

    def __init__(self, pin, proc_func):
        #pass init variables through to pushbutton class
        SonosHW.PushButton.__init__(self, pin, proc_func)
        self.button_duration=""

    def test(self, event):
        print(SonosHW.PushButton.button_duration(self, event))
        print('Event: ',event)
        # self.button_duration = SonosHW.PushButton.button_duration
        # print('Button Duration: ',self.button_duration)

    def get_sonos_units(self):
        unit_names =[]
        try:
            units = soco.discover(timeout=5)
            for (index, item) in enumerate(units):
                unit_names.append(item.player_name)
                print(unit_names[index])
            return unit_names
        except:
            print("could not get sonos units")
            return
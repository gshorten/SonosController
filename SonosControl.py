#!/usr/bin/env python

# Module with generic classes for controlling sonos system with raspberry pi + rotary encoders, switches, lcd displays, etc
#

import soco
import time
import RGBRotaryEncoder
import Adafruit_CharLCD as LCD

class SonosVolCtrl():
    # processes the callback from the rotary encoder to change the volume of the sonos unit
    # and does stuff when the encoder button is pressed (also via callbacks)

    def __init__(self, sonos_unit, vol_ctrl_led, up_increment = 4, down_increment = 5,):
        # sonos unit
        self.unit = sonos_unit
        self.upinc = up_increment       # how much to change the volume each click of the volume knob
        self.downinc = down_increment   # how much to change the volume down
        self.vol_ctrl_led = vol_ctrl_led

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
            print("new volume: ", new_volume)
        elif event == 2:
            # direction is counter clockwise, volume down
            # turn volume down more quickly than up, better for the user!
            new_volume = unit_volume - self.downinc
            if new_volume < 0:
                new_volume = 0
            self.unit.volume = new_volume
            print ("new volume: ", new_volume)

        elif event == 3 or event ==4:
            # these events are the rotary encoder button being pressed.
            # 3 is down, 4 is up
            # use a seperate def to figure out short or long press.
            if RGBRotaryEncoder.RotaryEncoder.get_button_press_duration(self,event) == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif RGBRotaryEncoder.RotaryEncoder.get_button_press_duration(self,event) == "long":
                try:
                    # long button press, skip to the next track
                    self.vol_ctrl_led.knob_led('off')
                    self.vol_ctrl_led.knob_led('on', 'blue')
                    print("Skipping to next track")
                    self.unit.next()
                except:
                    print("cannot go to next track with this source")


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


class PlaystateLED:
    # class to change the sonos volume rotary controller's LED depending on play_state and other things
    # but right now only can think of playstate
    # made it a class in case I think of other unit related things to show on the knob, like is unit in the current
    # group?

    def __init__(self, unit, led):
        self.unit = unit            #sonos unit we are checking for
        self.led = led              #led object on rotary controller

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
            self.led.knob_led('off', 'green')
            self.led.knob_led('on', 'red')
        elif play_state == "PLAYING":
            self.led.knob_led('off', 'red')
            self.led.knob_led('on', 'green')

        return

class TrackInfo:
    # methods for getting information about the current track, and for displaying info about the track on the lcd

    def __init__(self, unit):
        self.unit = unit

    def current_track_info(self):
        # returns a dictionary "currently_playing" with "title" and "from" (ie, station, artist) for the currently playing track
        # this is used to update the display, such as after adding a track to the queue or pausing / playing
        currently_playing = {'title': "", 'from': "", 'meta': ''}  # dictionary to store track information
        current_track = self.unit.get_current_track_info()
        # time.sleep(.1)  # pause long enough to get track info, probably don't need this
        try:
            if self.is_siriusxm(current_track):
                # check to see if it is a siriusxm source, if so, then get title and artist using siriusxm_track_info function
                current = self.siriusxm_track_info(current_track)
                currently_playing['title'] = current['xm_title']
                currently_playing['from'] = current['xm_artist']

            else:
                currently_playing['title'] = current_track['title']
                currently_playing['from'] = current_track['artist']

            if currently_playing['title'] == currently_playing['from']:  # if title and from are same just display title
                currently_playing['from'] = "                "

            if len(currently_playing['title']) > 40:
                currently_playing['title'] = 'getting title'
                currently_playing['from'] = 'getting from'

            currently_playing['meta'] = current_track['metadata']
            # meta data is  used in main loop to check if the track has changed
            return currently_playing
        except:
            currently_playing['title'] = 'gettimg title'
            currently_playing['from'] = 'getting artist'
            currently_playing['meta'] = ''
            return currently_playing

    def is_siriusxm(self, current_track):
        # tests to see if the current track is a siriusxm station
        s_title = current_track['title']
        s_title = s_title[0:7]

        if s_title == 'x-sonos':
            # only siriusxm stations seem to start this way
            return True
        else:
            return False

    def siriusxm_track_info(self, current_track):
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

        return track_info



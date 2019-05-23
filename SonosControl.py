#!/usr/bin/env python

"""
Module with generic classes for controlling sonos system with raspberry pi.

Works with rotary encoders, switches, lcd displays, etc
requires SonosHW.py module

Classes:
    SonosVolCtrl :      changes the volume of a sonos unit based on CW or CCW input, 
                        also pauses, plays when button pushed
    PlayStateLED:       changes colour of a tricolour LED depending on the playstate of a sonos unit.  Subclass of
                        SonosHW.TriColourLED.
    CurrentTrack:       class for the current sonos track (for a specified unit) Methods for getting title, artist
                        regardless of source
    SonosUnits:         all the sonos units, Methods for getting units, selecting active unit
    
Imports:
    soco               soco.SoCo project
    time
    SonosHW             part of this project
    
"""

import soco
import time
import SonosHW
import random
import tryagain


class SonosVolCtrl:
    """
    Controls the volume of the sonos unit, pauses, plays, skips tracks when volume button is pushed.

    processes the callback from the rotary encoder to change the volume of the sonos unit
        and does stuff when the encoder button is pressed (also via callbacks)
    """

    def __init__(self, units, lcd, vol_ctrl_led, up_increment = 4, down_increment = 5,):
        self.lcd = lcd
        # sonos unit
        self.units = units
        self.upinc = up_increment       # how much to change the volume each click of the volume knob
        self.downinc = down_increment   # how much to change the volume down
        self.vol_ctrl_led = vol_ctrl_led
        self.new_volume = 0
        self.volume_changed_time = 0
        self.button_down = 0
        self.button_up = 0

    def change_volume(self, direction):
        """
        Callback function to change the volume of the sonos unit
        is called from the RotaryEncoder class  when encoder is changed.
        direction is returned from the RotaryEncoder class, can be either CW(clockwise rotation) or CCW (counter cw)

        :param direction:       CW (clockwise) or CCW (counterclockwise)
        :type direction:        str
        :return:                none
        :rtype:                 none
        """
        # get the volume of the sonos unit
        unit_volume = self.units.active_unit.volume
        self.volume_changed_time = time.time()
        if direction == 'CW':
            # direction is clockwise
            self.new_volume = unit_volume + self.upinc
            if self.new_volume > 100:
                self.new_volume = 100
        elif direction == 'CCW':
            # direction is counter clockwise, volume down
            # turn volume down more quickly than up, better for the user!
            self.new_volume = unit_volume - self.downinc
            if self.new_volume < 0:
                self.new_volume = 0
        self.units.active_unit.volume = self.new_volume
        print ("new volume: ", self.new_volume)

    def pause_play_skip(self, duration):
        #pauses, plays, skips tracks when rotary encoder button is pressed.
        # callback from a button (usually the rotary encoder)
        try:
            if duration == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif duration == "long":
                try:
                    # long button press, skip to the next track
                    self.vol_ctrl_led.change_led('off')
                    self.vol_ctrl_led.change_led('on', 'blue')
                    print("Skipping to next track")
                    self.units.active_unit.next()
                except:
                    print("cannot go to next track with this source")
        except:
          print('pause_play error')

    def pause_play(self):
        try:
            # pauses or plays the sonos unit, toggles between the two.
            play_state = self.units.active_unit.get_current_transport_info()['current_transport_state']
            print(play_state)
            if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
                self.units.active_unit.play()
                print("Now Playing")
            elif play_state == "PLAYING":
                # unit is playing, stop it
                self.units.active_unit.pause()
                print("Now Paused")
        except:
            print("could not pause or play")


class PlaystateLED(SonosHW.TriColorLED):
    """
    Class for the LED on the volume knob.

    Methods to change the sonos volume rotary controller's LED depending on play_state and other things..
    """

    def __init__(self, units, green, red, blue):
        """
        :param units:       list of sonos units
        :type units:        object
        :param green:       pin number (BCM) for green led
        :type green:        int
        :param red:         pin number (BCM) for red led
        :type red:          int
        :param blue:        pin number (BCM) for blue led
        :type blue:         int
        """
        self.units = units           #sonos unit we are checking for
        # initialize the LED
        SonosHW.TriColorLED.__init__(self, green, red, blue)
        self.led_on_time = time.time()
        self.play_state = ""
        self.led_timeout = 1600

    def play_state_LED(self):
        # changes colour of light on encoder button depending on play state of the sonos unit
        try:
            unit_state = self.units.active_unit.get_current_transport_info()
            # determine if the sonos unit is playing or not
            self.play_state = unit_state['current_transport_state']

            if self.play_state == "PAUSED_PLAYBACK" or self.play_state == "STOPPED":
                paused = True
            else:
                paused = False
            on_time = time.time() - self.led_on_time
            if paused and on_time < self.led_timeout:
                # change the colour of the led
                # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
                self.change_led('off', 'green')
                self.change_led('on', 'red')
            elif paused and on_time > self.led_timeout:
                self.change_led('off', 'green')
                self.change_led('off','red')
                self.change_led('off', 'blue')
            elif self.play_state == "PLAYING" :
                self.change_led('off', 'red')
                self.change_led('on', 'green')
                self.led_on_time = time.time()
            return
        except:
            print('error in playstate led')


class CurrentTrack:
    """
    Class for current track.

    Methods:
        - track_info            returns a dictionary with title, artist, other data, depending source
        - display_track_info    displays track info, as long as display is not busy
        - is_siriusxm           checks to see if current track is siriusxm
        - siriusxm_track_info   extracts title, artist from a siriusxm source ( !@#$ it's in a different place
                                in the meta tag than for other sources)
    """

    def __init__(self, units, lcd):
        """
        :param units:       list of all sonos units
        :type units:        instance of SonosContol.SonosUnits
        :param lcd:         the lcd display to use
        :type lcd:          instance of desired lcd display
        """
        self.lcd = lcd
        # self.currently_playing = {'title': "", 'from': "", 'meta': ''}          # dictionary to store track information
        self.display_start_time = 0
        self.current_old = ""
        self.current_title = ""
        self.units = units
        self.current = ""
        self.currently_playing = {}


    def track_info(self):
        """
        Returns a dictionary "currently_playing" with "title" and "from"
            (ie, station, artist) for the currently playing track
            this is used to update the display, such as after adding a track to the queue or pausing / playing
        """
        return_info = {'track_title' : '', 'track_from' : '', 'meta' : ''}
        try:
            current = self.units.active_unit.get_current_track_info()
            #self.current_track = tryagain.call(self.units.active_unit.get_current_track_info(), max_attempts = 3, wait = 1)

            if self.is_siriusxm(current):
                # check to see if it is a siriusxm source,
                #   if so, then get title and artist using siriusxm_track_info function, because get_current_track_info
                #   does not work with Siriusxm tracks.
                current_sx = self.siriusxm_track_info(current=current)
                return_info['title'] = current_sx['xm_title']
                return_info['from'] = current_sx['xm_artist']
                print("siriusxm track, title:", return_info['title'])
            else:
                return_info['track_title'] = current['title']
                return_info['track_from'] = current['artist']
            if return_info['track_title'] == return_info['track_from']:  # if title and from are same just display title
                return_info['track_from'] = "                "
            return_info['meta'] = current['metadata']
            return return_info
        except:
            return_info['track_title'] = 'No Title :-('
            return_info['track_from'] = 'No Artist :-('
            return return_info


    def display_track_info(self):
        """
         Displays the current track if it has changed
        """

        # use tryagain if get_current_track_info fails, ie returns None
        # self.current_track = tryagain.call(self.units.active_unit.get_current_track_info(), max_attempts=3,wait=1)
        current_track = self.track_info()
        # check to see if we are doing something that we don't want to interrupt, or if the lcd is still (likely)
        # being written to.
        if self.lcd.is_busy():
            return
        if  current_track != self.current_old:
            print('track has changed')
            print(current_track['track_title'],"   ",current_track['track_from'])
            self.lcd.display_text(current_track['track_title'],current_track['track_from'])
            self.current_old = current_track

    def is_siriusxm(self, current):
        """
        tests to see if the current track is a siriusxm station
        """
        s_title = current['title']
        s_title = s_title[0:7]
        if s_title == 'x-sonos':
            # only siriusxm stations seem to start this way
            return True
        else:
            return False

    def siriusxm_track_info(self,current):
        """
        Extracts title and artist from siriusxm meta track data.

        We need to do this because get_current_track_info does not return 'title' or 'artist' for siriusxm sources,
        instead returns all the metadata for the track.  For some reason, who knows?

        :param current_track:   currently playing track
        :type current_track:
        :return:                dictionary with track information - title, artist
        :rtype:                 dict
        """
        # initialize dictionary to hold title and artist info
        track_info = {"xm_title": "", 'xm_artist': ''}

        try:
            # gets the title and artist for a sirius_xm track
            # title and artist stored in track-info dictionary
            meta = current['metadata']
            title_index = meta.find('TITLE') + 6
            title_end = meta.find('ARTIST') - 1
            title = meta[title_index:title_end]
            artist_index = meta.find('ARTIST') + 7
            artist_end = meta.find('ALBUM') - 1
            artist = meta[artist_index:artist_end]

            if title[0:9] == 'device.asp':  # some radio stations first report this as title, filter it out until title appears
                track_info['xm_title'] = "    "
                track_info['xm_artist'] = "   "
            else:
                track_info['xm_title'] = title
                track_info['xm_artist'] = artist
                return track_info
        except:
            track_info['xm_title'] = "no title"
            track_info['xm_artist'] = "no artist"
            return track_info


class SonosUnits:
    """
    The Sonos units available.  Selects the active unit using a pushbutton.

    Methods:
        - get_sonos_units         gets a list of the sonos units, and makes a list of their names
        - select_sonos_unit       selects a sonos unit using the pushbutton.  This method is called from a GPIO interrupt
                                generated by pushing a button.
    """

    def __init__(self, lcd, default_name):
        """
        :param lcd:             and lcd object
        :type lcd:              object
        :param default_name:    name of the default unit
        :type default_name:     str
        """

        self.unit_index = 0                 # counter for stepping through list
        self.active_unit_name = default_name
        self.lcd = lcd                      # the lcd display
        self.get_units_time = 0             # time that the sonos list was last updated
        self.first_time = True              # flag so that we get sonos list when button is pushed.
        self.active_unit = soco.discovery.by_name(default_name)  # get default unit
        # todo sometimes this fails, maybe use tryagain.  nb. need to use lambda form to pass parameter into tryagain
        if not self.active_unit == None:
            self.active_unit_name = self.active_unit.player_name
        self.selecting_unit = False
        self.units = list(soco.discover(timeout=20))

    def select_unit_single_press(self):
        """
        Cycles through sonos units, making each one the active unit in turn.  Called when a button is pressed.
        """
        try:
            if self.lcd.is_busy():
                #ignore the keypress, return - so we don't garble the display.
                return
            time_since_last = time.time() - self.get_units_time
            self.selecting_unit = True
            if time_since_last > 30:
                # if it's been more than 30 seconds since last push, show active unit, then current track
                self.lcd.display_text('Active Unit:', self.active_unit.player_name)
                if time.time() - self.get_units_time > 600:
                    #if it's been more than 10 minutes since last unit selection refresh list of units
                    # self.sonos_names = self.get_sonos_names()
                    # self.number_of_units = len(self.sonos_names)
                    self.get_units()
            elif time_since_last < 30:
                # cycle through units, make each one active
                self.unit_index += 1  # go to next sonos unit
                if self.unit_index >= self.number_of_units:
                    # if at end of units list set index back to 0
                    self.unit_index = 0
                self.active_unit = self.units[self.unit_index]
                self.active_unit_name = self.active_unit.player_name
                #self.active_unit = soco.discovery.by_name(self.active_unit_name)
                # give time to get current sonos unit
                print("Active Unit:", self.unit_index, 'Name: ', self.active_unit_name, "Unit: ", self.active_unit)
                self.lcd.display_text("Active Unit", self.active_unit_name, sleep = .05)

            self.get_units_time = time.time()
            self.selecting_unit = False
        except:
            print('could not change unit')

    def get_units(self):
        """
        Get list of sonos units
        :return:
        :rtype:
        """
        self.units = list(soco.discover(timeout=20))
        # nb soco.discover returns an unordered set, we need to convert to ordered list.
        self.number_of_units = len(self.units)
        self.get_units_time = time.time()
        print()
        print('List of Sonos Units and Names:')
        for i in self.units:
           print( '{0:4} {1:20} {2:8} {3:10}'.format('Name: ', i.player_name, "Address: ", i.ip_address ))


class WallboxPlayer:
    """
    Plays sonos tracks, main method called from SonosHW.Wallbox from GPIO threaded callback generated by the wallbox
    buttons - see Wallbox class in SonosHW for full explanation of how the wallbox interface works.
    """
    def __init__(self, units, current_track,  lcd):
        """
        :param units:               The Sonos units
        :type units:                object
        :param current_track:       The current track / selection playing
        :type current_track:
        :param lcd:                 The lcd display
        :type lcd:                  object
        """
        self.playing = 'radio'
        self.last_song_played = ''
        self.units = units
        self.active_unit = units.active_unit
        self.lcd = lcd
        self.current_track = current_track

    def play_playlist(self, number):
        #  play sonos playlists by index number
        global queue_length, new_track, playing
        self.active_unit.clear_queue()
        my_playists = self.active_unit.music_library.get_music_library_information('sonos_playlists')
        curr_playlist = my_playists[number]
        # get the name of the playlist
        playlist_name = str(curr_playlist)
        playlist_name = playlist_name[26:(len(playlist_name) - 17)]
        print("Playing playlist: ", playlist_name)

        self.active_unit.add_to_queue(curr_playlist)
        # select a random track to start playing
        # first get length of queue
        queue_length = self.active_unit.queue_size
        starting_song = random.randint(1, queue_length - 1)
        self.active_unit.play_from_queue(starting_song)
        # start playing any random song in the queue

        self.active_unit.play_mode = 'shuffle_norepeat'
        playing = 'playlist'
        self.lcd.display_text("Playlist Playing:", playlist_name, 3)

    def play_radiostation(self, number):
        """
        Play a radio station (sonos favorite 0 - 9 )
        :param number:             wallbox selection 0-9
        :type number:               int
        :return:                    plays selected station on active unit
        :rtype:
        """

        try:
            favorites = self.active_unit.get_sonos_favorites(0, 20)
            favlist = favorites[
                'favorites']  # get favorit5es dictionary,'favorites' is the key for the list of favorites
            favuri = favlist[number]["uri"]
            favmeta = favlist[number]["meta"]
            favtitle = favlist[number]["title"]
            radio_station = favtitle[4:]
            print("playing: ", radio_station)

            # unit.clear_queue()
            self.active_unit.play_uri(favuri, favmeta)
            self.lcd.display_text('Playing Radio:', radio_station, 3)
            self.playing = 'radio'
        except:
            # lcd_display('I fucked up', 'segmentation fault',3)
            self.lcd.display_text('Try Again', 'nothing', 3)

    def play_selection(self, wallbox_number):
        """
        Plays a selection based on the wallbox number.  This def is called from SonosHW.Wallbox
        """
        #global last_song_played, playing, display_pause
        if wallbox_number <= 9:
            # if the item is 0 - 9 play radio stationsif not first_pulse:
            # if it is the second pulse we can time the gap
            self.play_radiostation(wallbox_number)
            self.active_unit.clear_queue()
            self.playing = 'radio'
        elif wallbox_number > 9 and wallbox_number <= 19:
            # if the item is 10 - 19 play playlists
            playlist_number = wallbox_number - 10
            self.active_unit.clear_queue()
            self.play_playlist(playlist_number)
            self.playing = 'playlist'
            now_playing = self.current_track.currently_playing
            print("Playing Playlist Song: ", now_playing['title'], 'by', now_playing['from'])

        elif wallbox_number > 19:
            """ 
            UI Logic for playing song selections:
            1) If a sonos playlist or  a radio station was playing before, then we clear the queue and add
            a song.
            2) if the  queue is already playing, we add to the queue.
            """
            print("Item Number: ", wallbox_number)
            self.active_unit.play_mode = 'normal'
            # get the sonos track to play:
            track_selection = self.get_playlist_track('Jukebox.m3u', wallbox_number - 20)

            if self.playing == 'playlist' or self.playing == 'radio':
                # if radio or playlist was playing assume that we want  to start a new queue
                self.active_unit.clear_queue()
                self.active_unit.add_to_queue(track_selection)
                self.active_unit.play_from_queue(0)
                print("Added Song to Queue:", self.song_title(track_selection))
                self.lcd.display_text('Added to Queue', self.song_title(track_selection), 4)
            else:
                # if the queue was already playing we just add to the queue
                self.active_unit.add_to_queue(track_selection)
                self.active_unit.play()
                print("Added Song to Queue:", self.song_title(track_selection))
                self.lcd.display_text('Added to Queue', self.song_title(track_selection), 4)
            self.playing = 'queue'
        current = self.current_track.currently_playing
        self.lcd.display_text(current['title'], current['from'], 1)

    def song_title(self,track_selection):
        # function to strip out song title from currently playing track
        track_name = str(track_selection)
        track_name = track_name[19:(len(track_name) - 17)]
        return track_name

    def get_playlist_track(self, target_playlist, trackno):
        # gets the playlist track item
        try:
            curr_playlists = self.active_unit.music_library.get_music_library_information('playlists',
                             search_term=target_playlist, complete_result=True)
            curr_playlist = curr_playlists[0]
            curr_playlist_tracks = self.active_unit.music_library.browse(curr_playlist, 0, 200)
            curr_playlist_track = curr_playlist_tracks[trackno]
            return curr_playlist_track
        except:
            print('Something went wrong')
            self.lcd.display_text("Could not play", 'Try again', 3)

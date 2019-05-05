#!/usr/bin/env python

"""
Module with generic classes for controlling sonos system with raspberry pi.

works with rotary encoders, switches, lcd displays, etc
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


class SonosVolCtrl():
    """
    Controls the volume of the sonos  unit.

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
        callback function to change the volume of the sonos unit
        is called from the RotaryEncoder class
        event is returned from the RotaryEncoder class, can be either CW(clockwise rotation) or CCW (counter cw)
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

    def display_volume(self):
        time_since_last_vol_change = time.time() - self.volume_changed_time
        if time_since_last_vol_change > 3 and time_since_last_vol_change < 5:
            print('should be displaying the volume')
            self.lcd.display_text('volume is: ', str(self.new_volume), timeout=3)
            time.sleep(1)
            #self.vol_ctrl_lcd.display_track_info()
            self.lcd.display_track_info(30)

    def pause_play(self):
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


class PlaystateLED(SonosHW.TriColorLED):
    """
    Class to change the sonos volume rotary controller's LED depending on play_state and other things.

    but right now only can think of playstate
    made it a class in case I think of other unit related things to show on the knob, like is unit in the current
    group?
    btw it is a subclass
    """

    def __init__(self, units, green, red, blue):
        self.units = units           #sonos unit we are checking for
        SonosHW.TriColorLED.__init__(self, green, red, blue)

    def play_state_LED(self):
        # changes colour of light on encoder button depending on play state of the sonos unit

        unit_state = self.units.active_unit.get_current_transport_info()
        time.sleep(2)  # pause long enough for sonos to respond
        # todo play with this, we might not need it
        # determine if the sonos unit is playing or not
        play_state = unit_state['current_transport_state']
        if play_state == "PAUSED_PLAYBACK" or play_state == "STOPPED":
            # change the colour of the led
            # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
            self.change_led('off', 'green')
            self.change_led('on', 'red')
        elif play_state == "PLAYING":
            self.change_led('off', 'red')
            self.change_led('on', 'green')
        return


class CurrentTrack:
    """
    Class for current track, has method to display current track as well.



    """


    def __init__(self, units, lcd):
        self.lcd = lcd
        self.currently_playing = {'title': "", 'from': "", 'meta': ''}          # dictionary to store track information
        self.display_start_time = 0
        self.old_title=""
        self.current_title = ""
        self.units = units                                                     # list of sonos  units

    def track_info(self):
        """
        Returns a dictionary "currently_playing" with "title" and "from"
            (ie, station, artist) for the currently playing track
            this is used to update the display, such as after adding a track to the queue or pausing / playing
        """

        try:
            self.current_track = self.units.active_unit.get_current_track_info()
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

    def display_track_info(self, timeout=10):
        # displays the current track if it has changed
        current = self.track_info()
        if current['title'] == self.old_title:
            return
        else:
            print('track has changed')
            print(current['title'],"   ",current['from'])
            self.lcd.display_text(current['title'], current['from'], timeout)
            self.old_title = current['title']

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
        track_info =[]
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


class SonosUnits():
    """
    selects the active unit using a pushbutton)
    
    Methods:
        get_sonos_units         gets a list of the sonos units, and makes a list of their names
        select_sonos_unit       selects a sonos unit using the pushbutton
        
    Attributes
        lcd                     an lcd object
        default unit            the name of a sonos unit to use as default until a different one is selected
    
    """

    def __init__(self, lcd, default_unit):

        self.unit_names = []                # list of sonos unit names
        self.unit_index = 0                 # counter for stepping through list
        self.active_unit_name = default_unit
        self.lcd = lcd                      # the lcd display
        self.selected_unit_name = ''             # currently selected (but not yet active) unit attribute
        self.get_units_time = 0             # time that the sonos list was last updated
        self.first_time = True              # flag so that we get sonos list on starutp
        self.sonos_names = self.get_sonos_units()
        self.number_of_units = len(self.sonos_names)
        self.led_type = 'active'            # flag for encoder led to show playstate of active unit; other is 'selected'
        self.selected_unit_name = self.active_unit_name

        self.active_unit = soco.discovery.by_name(self.active_unit_name)  # get default sonos unit
        time.sleep(2)
        print("initializing active unit: ", self.active_unit)

    def get_sonos_units(self):
        """
        Gets a list of sonos units and a lis of thier names
        """

        #reset list of names; it might have changed!, ie units turned off or disconnected
        unit_names = []
        try:
            units = soco.discover(timeout=20)
            # get sonos units; leave long timeout - sometimes it takes a long time to get list
            # next make list of sonos unit names
            for (index, item) in enumerate(units):
                unit_names.append(item.player_name)
                print(unit_names[index])
            return unit_names
        except:
            print("could not get sonos units")
            self.active_unit = soco.discovery.by_name('Portable')
            return

    def select_sonos_unit(self, button_type):
        # callback from button press GPIO event
        try:
            if time.time() - self.get_units_time > 600 or self.first_time:
                # if this is the first time (starting up) or longer than 10 minutes get list of sonos units
                # otherwise we work from previous list - this makes ui more responsive but risk fail to select
                #   unit if it is no longer available or turned on.
                self.sonos_names = self.get_sonos_units()
                self.number_of_units = len(self.sonos_names)
                # start timer for when we got list
                self.get_units_time = time.time()
                current_unit_display = str(self.active_unit.player_name)
                self.lcd.display_text('Current Unit', current_unit_display, timeout=20,sleep=3)
                time.sleep(3)
                # give time to read message
                self.first_time = False
                # not the first time (start up) any more.
                # need to sleep a little so we can see the current unit info.
                print ('number of units', self.number_of_units)
            if button_type == 'short':
                # get current sonos player from list of sonos units
                self.selected_unit_name = self.sonos_names[self.unit_index]
                self.selected_unit = soco.discovery.by_name(self.selected_unit_name)
                # give time to get current sonos unit
                time.sleep(1)
                self.led_type = "selected"
                print("Selected Unit:", self.unit_index,'Name: ',self.sonos_names[self.unit_index])
                selected_unit_display_text = 'for ' + str(self.selected_unit_name)
                self.lcd.display_text(selected_unit_display_text, 'press + hold', timeout=20)
                #time.sleep(1)
                # give time to read message, as track has also changed; display_track_info will update display!
                # if this push is within x seconds of the last push then
                # cycle through the units
                self.unit_index += 1  # go to next sonos unit
                if self.unit_index >= self.number_of_units:
                    # if at end of units list set index back to 0
                    self.unit_index = 0
            elif button_type == 'long':
                # long press selects the unit
                # make the selected_unit the active unit
                try:
                    self.active_unit_name = soco.discovery.by_name(self.selected_unit_name)
                    # need a little time to get the unit, sometimes
                    time.sleep(2)
                except:
                    print('could not get active unit')
                    return
                self.led_type = 'active'
                display_playing = str(self.active_unit.player_name)
                self.lcd.display_text('Playing: ', display_playing, timeout=10,)
                # give time to read message, as track has also changed; display_track_info will update display!
                time.sleep(4)
                print('Active Unit: ', display_playing)
                return
        except:
            print("select sonos unit failed")
            return


class WallboxPlayer():
    """
    Plays sonos tracks, main method called from SonosHW.Wallbox from GPIO threaded callback.
    """

    def __init__(self, units, lcd):
        self.playing = 'radio'
        self.last_song_played = ''
        self.units = units
        self.active_unit = units.active_unit
        self.lcd = lcd


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
        # play a radio station (sonos favorite 0 - 9 )

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
            now_playing = self.current_track_info()
            print("Playing Playlist Song: ", now_playing['title'], 'by', now_playing['from'])

        elif wallbox_number > 19:
            print("Item Number: ", wallbox_number)
            '''
            UI Logic for playing song selections:
            1) If a sonos playlist or  a radio station was playing before, then we clear the queue and add
            a song.
            2) if the  queue is already playing, we add to the queue.
            '''
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
        current = self.current_track_info()
        self.lcd.display_text(current['title'], current['from'], 1)

    def song_title(self,track_selection):
        # function to strip out song title from currently playing track
        track_name = str(track_selection)
        track_name = track_name[19:(len(track_name) - 17)]
        return track_name

    def get_playlist_track(self, target_playlist, trackno):
        # gets the playlist track item
        try:
            curr_playlists = self.active_unit.music_library.get_music_library_information('playlists', search_term=target_playlist,
                                                                              complete_result=True)
            curr_playlist = curr_playlists[0]
            curr_playlist_tracks = self.active_unit.music_library.browse(curr_playlist, 0, 200)
            curr_playlist_track = curr_playlist_tracks[trackno]
            return curr_playlist_track
        except:
            print('Something went wrong')
            self.lcd.display_text("Could not play", 'Try again', 3)

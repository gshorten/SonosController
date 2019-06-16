#!/usr/bin/env python

"""
Module with generic classes for controlling sonos system with raspberry pi.

Works with rotary encoders, switches, display displays, etc
requires SonosHW.py module

Classes:
    SonosVolCtrl :          changes the volume of a sonos unit based on CW or CCW input,
                            also pauses, plays when button pushed
    PlayStateLED:           changes colour of a tricolour LED depending on the playstate of a sonos unit.  Subclass of
                            SonosHW.TriColourLED.
    SonosDisplayUpdater:    updates the two line displays and playstate led when the sonos track changes
    SonosUnits:             all the sonos units, Methods for getting units, selecting active unit
    
Imports:
    soco               soco.SoCo project
    time
    SonosHW             part of this project, has classes for the hardware (displays, switches, wallbox)
    SonosUtils          utility defs (no classes)
    
"""

import soco
import time
import SonosHW
import random
import SonosUtils
from soco import events_twisted
from twisted.internet import reactor
soco.config.EVENTS_MODULE = events_twisted

class SonosDisplayUpdater:
    """
    Displays the title and artist of the current track when it changes, updates the playstate LED as well

    Uses twisted to call a callback when a track changes, this eliminates the polling we were having to do before :-)
    """
    # set the events module in soco to use the twisted version

    def __init__(self, units, display, led):
        """
        :param units:         sonos units
        :type units:          object
        :param display:       the display we are using
        :type display:        object
        """
        self.device = units.active_unit
        self.display = display
        self.led = led

    def display_new_track_info(self, event):
        """
        Displays the new track info on the display, and updates the playstate LED.  Assumes display is two line type
        :param event:       The sonos transport state info
        :type event:        dict
        :return:            none
        :rtype:             none
        """
        try:
            transport_state = event.variables['transport_state']
            track_info = SonosUtils.getTitleArtist(unit=self.device)
            print()
            print('*************** Changed *************')
            print('          ', time.asctime())
            print('Transport State: ', transport_state)
            print('Track Info: ', track_info['track_title'], "  ", track_info['track_from'])
            if transport_state == 'STOPPED':
                self.display.display_text("Sonos is", "Stopped", sleep=3)
                self.led.show_playstate(transport_state)
                # display for 10 seconds then turn off backlight.  Don't need it when nothing is playing.
                # self.display.color = (0,0,0)
            else:              		
                self.display.display_text(track_info['track_title'],track_info['track_from'])
                self.led.show_playstate(transport_state)

        except Exception as e:
            print('There was an error in display_new_track:', e)

    def main(self):
        sub = self.device.avTransport.subscribe().subscription
        sub.callback = self.display_new_track_info

        def before_shutdown():
            sub.unsubscribe()
            events_twisted.event_listener.stop()

        reactor.addSystemEventTrigger(
            'before', 'shutdown', before_shutdown)


class SonosVolCtrl:
    """
    Controls the volume of the sonos unit, pauses, plays, skips tracks when volume button is pushed.

    processes the callback from the rotary encoder to change the volume of the sonos unit
        and does stuff when the encoder button is pressed (also via callbacks)
    """

    def __init__(self, units, display, vol_ctrl_led, up_increment = 4, down_increment = 5, ):
        self.lcd = display
        # sonos unit
        self.units = units
        self.upinc = up_increment       # how much to change the volume each click of the volume knob
        self.downinc = down_increment   # how much to change the volume down
        self.vol_ctrl_led = vol_ctrl_led
        self.new_volume = 0
        self.volume_changed_time = 0
        self.button_down = 0
        self.button_up = 0

    def change_group_volume(self, direction):
        """
        Callback, changes volume of all members of the active group

        :param direction:
        :type direction:
        :return:
        :rtype:
        """
        if direction == 'CW': volume_change = self.upinc
        else: volume_change = -self.downinc

        for each_unit in self.units.active_unit.group:
            each_unit.volume += volume_change

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
        if direction =='CW' :
            volume_change = self.upinc
        else:
            volume_change = -self.downinc
        self.units.active_unit.volume += volume_change
        # self.display_volume()
        
    def display_volume(self):
        """
        Displays the unit volume
        """
        # get the volume of sonos unit
        unit_volume = self.units.active_unit.volume
        self.lcd.display_text('Volume is:',unit_volume)
        print('Volume changed:', unit_volume)

    def pause_play_skip(self, duration):
        #pauses, plays, skips tracks when rotary encoder button is pressed.
        # callback from a button (usually the rotary encoder)
        try:
            if duration == 'short':
                # short button press, pause or play sonos unit
                self.pause_play()
            elif duration == "long":
                try:
                    # long button press, skip to the next track, turn LED blue
                    # TODO use event subscription to change LED
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

    def __init__(self, units, green, red, blue, on="low"):
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
        SonosHW.TriColorLED.__init__(self, green, red, blue, on)
        self.led_on_time = time.time()
        self.led_timeout = 1600

    def show_playstate(self,play_state):
        # changes colour of light on encoder button depending on play state of the sonos unit
        try:
            on_time = time.time() - self.led_on_time
            if play_state == "STOPPED" and on_time < self.led_timeout:
                # change the colour of the led
                # knob_led is the method in RGBRotaryEncoder module, KnobLED class that does this
                print('unit is stopped, led is red')
                self.change_led('on', 'red')
            elif play_state == "STOPPED" and on_time > self.led_timeout:
                print('timeout, led is off')
                self.change_led('off', 'green')
                self.change_led('off','red')
                self.change_led('off', 'blue')
            elif play_state == "PLAYING":
                print('unit is playing, led is green')
                # print( 'turning led to green')
                self.change_led('on', 'green')
            elif play_state == "TRANSITIONING":
                print('unit is transitioning, led is blue')
                self.change_led('on', 'blue')
            self.led_on_time = time.time()
            return
        except:
            print('error in playstate led')


class SonosUnits:
    """
    The Sonos units available.  Selects the active unit using a pushbutton.

    Methods:
        - get_sonos_units         gets a list of the sonos units, and makes a list of their names
        - select_sonos_unit       selects a sonos unit using the pushbutton.  This method is called from a GPIO interrupt
                                generated by pushing a button.
    """

    def __init__(self, display, default_name):
        """
        :param display:             an display object
        :type display:              object
        :param default_name:    name of the default unit
        :type default_name:     str
        """

        self.unit_index = 0                 # counter for stepping through list
        self.active_unit_name = default_name
        self.display = display                      # the display display
        self.get_units_time = 0             # time that the sonos list was last updated
        self.first_time = True              # flag so that we get sonos list when button is pushed.
        self.active_unit = self.get_default_unit(default_name, tries=3,wait=2)
        self.units = list(soco.discover(timeout=20))
        self.selected_unit = self.active_unit
        self.selected_unit_name = self.active_unit_name
				

    def get_default_unit(self,default_name, tries=4, wait=3):
        """
        Gets the default unit, if result is 'None' the tries up to <tries> times and waits <wait> between tries
        :param default_name:    Name of the sonos unit we are looking for
        :type default_name:     str
        :return:                Soco object
        :rtype:                 object
        """
				
        for x in range(tries):
            active = soco.discovery.by_name(default_name)
            if active is not None: break
            time.sleep(wait)
        print("active Unit:", active.player_name, "tried ", x + 1, 'times')
        return active

    def group_units(self, duration):
        """
        Adds units to the group controlled by the kitchen master.  Called by the select unit pushbutton

        Short press cycles through units, long press adds to the group.  If a unit is already in a group, the long press
        removes it from the group
        :return:
        :rtype:
        """
        try:
            if duration == "short":
                #if it's been more than  minutes since we last pushed the button then refresh the list of units
                if time.time() - self.get_units_time > 600:
                    self.get_units()
                    self.get_units_time = time.time()

                # cycle through units, make each one active
                self.unit_index += 1  # go to next sonos unit

                if self.unit_index >= self.number_of_units:
                    # if at end of units list set index back to 0
                    self.unit_index = 0
                self.selected_unit = self.units[self.unit_index]
                if self.selected_unit == self.active_unit:
                    # skip the active unit (kitchen or other "default" unit)
                    self.unit_index += 1
                    self.selected_unit = self.units[self.unit_index]
                self.selected_unit_name = self.selected_unit.player_name
                print("Selected Unit:", self.unit_index, 'Name: ', self.selected_unit_name, "Unit: ", self.selected_unit)
                print("is a member of:", self.selected_unit.group.coordinator)

                if self.selected_unit.group.coordinator == self.active_unit.group.coordinator:
                    # if it is already in the group then give option to ungroup
                    print(self.selected_unit_name,"is already grouped")
                    self.display.display_text(self.selected_unit_name, "Hold > Un Group")
                self.display.display_text(self.selected_unit_name, "Hold > Group")
            if duration == "long":
                if self.selected_unit.group.coordinator == self.active_unit.group.coordinator:
                    self.selected_unit.unjoin()
                    print(self.selected_unit_name, "has left Kitchen")
                    self.display.display_text(self.selected_unit_name, "Un Grouped")
                else:
                    self.selected_unit.join(self.active_unit)
                    print(self.selected_unit_name,"joined to group")
                    self.display.display_text(self.selected_unit_name, "Added to Group")
            self.get_units_time = time.time()

        except:
            print('could not group or ungroup unit')


    def select_unit_single_press(self):
        """
        Cycles through sonos units, making each one the active unit in turn.  Called when a button is pressed.
        """
        try:
            if self.display.is_busy():
                #ignore the keypress, return - so we don't garble the display.
                return
            time_since_last = time.time() - self.get_units_time
            self.selecting_unit = True
            if time_since_last > 30:
                # if it's been more than 30 seconds since last push, show active unit, then current track
                self.display.display_text('Active Unit:', self.active_unit_name)
                if time.time() - self.get_units_time > 600:
                    # if it's been more than 10 minutes since last unit selection refresh list of units
                    self.get_units()
            elif time_since_last < 30:
                # cycle through units, make each one active
                self.unit_index += 1  # go to next sonos unit
                if self.unit_index >= self.number_of_units:
                    # if at end of units list set index back to 0
                    self.unit_index = 0
                self.active_unit = self.units[self.unit_index]
                self.active_unit_name = self.active_unit.player_name
                print("Active Unit:", self.unit_index, 'Name: ', self.active_unit_name, "Unit: ", self.active_unit)
                self.display.display_text('Active Unit', self.active_unit_name)

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
           print( '{0:20} {1:8} {2:10}'.format( i.player_name, "Address: ", i.ip_address ))
        print()


class WallboxPlayer:
    """
    Plays sonos tracks, main method called from SonosHW.Wallbox from GPIO threaded callback generated by the wallbox
    buttons - see Wallbox class in SonosHW for full explanation of how the wallbox interface works.
    """
    def __init__(self, units, display):
        """
        :param units:               The Sonos units
        :type units:                object
        :param current_track:       The current track / selection playing
        :type current_track:
        :param display:                 The display display
        :type display:                  object
        """
        self.playing = 'radio'
        self.last_song_played = ''
        self.units = units
        self.active_unit = self.units.active_unit
        self.display = display

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
        self.display.display_text("Playlist Playing:", playlist_name, 3)

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
            self.display.display_text('Playing Radio:', radio_station, 3)
            self.playing = 'radio'
        except:

            self.display.display_text('Try Again', 'nothing', 3)

    def play_selection(self, wallbox_number):
        """
        Plays a selection based on the wallbox number.  This def is called from SonosHW.Wallbox
        """

        if wallbox_number <= 9:
            # if the item is 0 - 9 play radio stationsif not first_pulse:
            # if it is the second pulse we can time the gap
            self.play_radiostation(wallbox_number)
            self.active_unit.clear_queue()
            self.playing = 'radio'
        elif 9 < wallbox_number <= 19:
            # if the item is 10 - 19 play playlists
            playlist_number = wallbox_number - 10
            self.active_unit.clear_queue()
            self.play_playlist(playlist_number)
            self.playing = 'playlist'
            now_playing = SonosUtils.getTitleArtist(self.active_unit)
            print("Playing Playlist Song: ", now_playing['track_title'], 'by', now_playing['track_from'])

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
                self.display.display_text('Added to Queue', self.song_title(track_selection), 4)
            else:
                # if the queue was already playing we just add to the queue
                self.active_unit.add_to_queue(track_selection)
                self.active_unit.play()
                print("Added Song to Queue:", self.song_title(track_selection))
                self.display.display_text('Added to Queue', self.song_title(track_selection), 4)
            self.playing = 'queue'

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
            self.display.display_text("Could not play", 'Try again', 3)

from __future__ import print_function
import logging
logging.basicConfig()
import soco
from pprint import pprint
from soco import events_twisted
soco.config.EVENTS_MODULE = events_twisted
from twisted.internet import reactor
import time
import SonosControl

class UpdateDisplay:
    """
    testing callback
    """

    def __init__(self,default):
        self.device = soco.discovery.by_name(default)
        self.playstate = ''
        self.track_info = []
        self.meta_old = ''
        self.transport_state_old = ''

    def do_stuff(self,event):
        try:
            self.meta = event.variables['current_track_meta_data']
            self.transport_state = event.variables['transport_state']
            self.track_info = CurrentTrack.track_info(unit=self.device)
            print('*************** Changed *************')
            print('Meta: ', self.meta)
            print('Transport State: ',self.transport_state)
            print('Track Info: ', self.track_info)
        except Exception as e:
            print ('There was an error in print_event:', e)

    def main(self):
        # pick a device at random and use it to get
        # the group coordinator
        #device = soco.discovery.by_name('Portable')
        print (self.device.player_name)
        # sub = device.renderingControl.subscribe().subscription
        sub2 = self.device.avTransport.subscribe().subscription
        # sub.callback = print_event
        sub2.callback = self.do_stuff
        def before_shutdown():
            # sub.unsubscribe()
            sub2.unsubscribe()
            soco.events_twisted.event_listener.stop()
        reactor.addSystemEventTrigger(
            'before', 'shutdown', before_shutdown)

class CurrentTrack:
    """
    Information for the current track.

    Methods:
        - track_info            returns a dictionary with title, artist, other data, depending source
        - display_track_info    displays track info, as long as display is not busy
        - is_siriusxm           checks to see if current track is siriusxm
        - siriusxm_track_info   extracts title, artist from a siriusxm source ( !@#$ it's in a different place
                                in the meta tag than for other sources)
    """

    def __init__(self):
        """
        :param units:           list of all sonos units
        :type units:            object
        :param display:         the display display to use
        :type display:          object
        """

        self.display_start_time = 0
        self.current_old = ""
        self.current_title = ""
        self.current = ""
        self.currently_playing = {}


    def track_info(unit):
        """
        Returns a dictionary "currently_playing" with "title" and "from"
            (ie, station, artist) for the currently playing track
            this is used to update the display, such as after adding a track to the queue or pausing / playing
        """
        return_info = {'track_title' : '', 'track_from' : '', 'meta' : ''}
        try:
            for x in range(3):
                # make 3 attempts to get track info
                current = unit.get_current_track_info()
                # print('got track info', current)
                # if we get something back then exit loop
                if current is not None: break
                # wait for 1 second before we try again
                time.sleep(1)
            # if we get nothing back fill in place holders for
            if current is None:
                print('got no track info')
                return_info['track_title'] = 'Title N/A'
                return_info['track_from'] = 'From N/A'
                return_info['meta'] = ""
                return return_info

            if CurrentTrack.is_siriusxm(current):
                # check to see if it is a siriusxm source,
                #   if so, then get title and artist using siriusxm_track_info function, because get_current_track_info
                #   does not work with Siriusxm tracks.
                current_sx = CurrentTrack.siriusxm_track_info(current_xm = current)
                return_info['track_title'] = current_sx['xm_title']
                return_info['track_from'] = current_sx['xm_artist']
                # print("siriusxm track, title:", return_info['track_title'], return_info['track_from'])
            else:
                return_info['track_title'] = current['title']
                return_info['track_from'] = current['artist']
            if return_info['track_title'] == return_info['track_from']:  # if title and from are same just display title
                return_info['track_from'] = "                "
            return_info['meta'] = current['metadata']
            # print('updated track info:', return_info['track_title'],"  ", return_info['track_from'])
            return return_info
        except:
            return_info['track_title'] = 'No Title :-('
            return_info['track_from'] = 'No Artist :-('
            return return_info


    # def display_track_info(self):
    #     """
    #      Displays the current track if it has changed
    #     """
    #
    #     current_track = self.track_info()
    #     # check to see if we are doing something that we don't want to interrupt, or if the display is still (likely)
    #     # being written to.
    #     if self.display.is_busy():
    #         return
    #     if  current_track != self.current_old:
    #         print('track has changed')
    #         print(current_track['track_title'],"   ",current_track['track_from'])
    #         self.display.display_text(current_track['track_title'], current_track['track_from'])
    #         self.current_old = current_track

    def is_siriusxm(current):
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

    def siriusxm_track_info(current_xm):
        """
        Extracts title and artist from siriusxm meta track data.

        We need to do this because get_current_track_info does not return 'title' or 'artist' for siriusxm sources,
        instead returns all the metadata for the track.  For some reason, who knows?

        :param current_xm:   currently playing track
        :type current_xm:
        :return:                dictionary with track information - title, artist
        :rtype:                 dict
        """
        # initialize dictionary to hold title and artist info
        track_info = {"xm_title": "", 'xm_artist': ''}

        try:
            # gets the title and artist for a sirius_xm track from metadata
            # title and artist stored in track-info dictionary

            meta = current_xm['metadata']
            title_index = meta.find('TITLE') + 6
            title_end = meta.find('ARTIST') - 1
            title = meta[title_index:title_end]
            artist_index = meta.find('ARTIST') + 7
            artist_end = meta.find('ALBUM') - 1
            artist = meta[artist_index:artist_end]

            if title[0:9] == 'device.asp' or len(title) > 30:

                # some radio stations first report this as title, filter it out until title appears
                track_info['xm_title'] = "No Title"
                track_info['xm_artist'] = " No Artist"
            else:
                track_info['xm_title'] = title
                track_info['xm_artist'] = artist
            return track_info
        except:
            track_info['xm_title'] = "no title"
            track_info['xm_artist'] = "no artist"
            return track_info

Update = UpdateDisplay('Portable')

if __name__=='__main__':
    reactor.callWhenRunning(Update.main)
    reactor.run()
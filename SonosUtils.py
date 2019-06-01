
import math
import time
import soco

"""
Module contains common utility functions for working with the Sonos system.

"""


def center_text(text):
    """
    Truncates text, centers it, converts to a string.

    :param  text:   text to be centered and truncated
    :type   text:   string
    """

    text_length = len(text)
    if text_length > 16:
        # truncate text if it is too long
        # also convert to a string for good measure, in case we pass an object!
        text = str(text[0:15])
    # calculate how much padding is required to fill display
    padding = math.ceil((16 - text_length) / 2)
    padding_text = " " * (padding)
    # pad the display text to center it.
    display_text = padding_text + text + padding_text
    # make sure it is still 16 characters long; take the first 16 characters
    display_text = display_text[0:15]
    return display_text


def getTitleArtist(unit):
    """
    Returns a dictionary "currently_playing" with "title" and "from"
        (ie, station, artist) for the currently playing track
        this is used to update the display, such as after adding a track to the queue or pausing / playing
    :param unit:    a sonos unit
    :type   unit:   soco object
    """
    return_info = {'track_title': '', 'track_from': '', 'meta': ''}

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

    def siriusxm_track_info( current_xm):
        """
        Extracts title and artist from siriusxm meta track data.

        We need to do this because get_current_track_info does not return 'title' or 'artist' for siriusxm sources,
        instead returns all the metadata for the track.  For some reason, who knows?

        :param current_xm:      currently playing track
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

    try:
        for x in range(3):
            # make 3 attempts to get track info
            current = unit.soco.get_current_track_info()
            print('got track info', current)
            #if we get something back then exit loop
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

        if is_siriusxm(current):
            # check to see if it is a siriusxm source,
            #   if so, then get title and artist using siriusxm_track_info function, because get_current_track_info
            #   does not work with Siriusxm tracks.
            current_sx = siriusxm_track_info(current_xm=current)
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

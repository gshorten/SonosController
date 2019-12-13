
import math
import time
import soco
import gpiozero
import requests
import json
from jsoncomment import JsonComment

"""
Module contains common utility functions for working with the Sonos system.

"""

def split_text(text, no_lines=2, line_length=22, centering_on=True):
    """
    Splits a line of text over specified number of lines, does not split words.  If more lines are specified
    than needed then the unused lines are blank. Lines are split to fit in line_length without breaking up words
    :param text:        text to be split
    :type text:         str
    :param lines:       number of lines to split text over
    :type lines:        int
    :param line_length: length of each line, in characters; usually the width of the display
    :type line_length:  int
    :param centering_on:    if True then text is centered in each line
    :type centering_on:     bool
    :return:            list of lines split to right length, list is no_lines long.
    :rtype:             list
    """
    # initialize list of lines
    lines = [''] * no_lines
    # get list of words
    text_parts = text.split()
    # initialize counters
    last_counter = 0
    counter=0
    x=0

    while True:
        # loop and build up sentence word by word; check each loop to see if sentence is wider than line_length
        lines[x] = ' '.join(text_parts[last_counter:counter])
        if len(lines[x]) > line_length :
            # take one word off the end of lines[x], make lines[x] shorter (or same length) as line_length
            lines[x] = ' '.join(text_parts[last_counter:counter-1])
            if centering_on:
                lines[x] = '{:^{width}}'.format(lines[x], width=line_length)
            last_counter = counter - 1
            x += 1
        counter += 1
        # check to see if it is the last line, if True then return and break.
        if counter > len(text_parts) or x == no_lines:
            return lines
            break


def center_text(text, display_char=16):
    """
    Truncates text, centers it, converts to a string.

    :param  text:           text to be centered and truncated
    :type   text:           string
    :param  display_char:   the display width, in characters
    :type   display_char:   int
    """
    # make sure text is a string, in case we passed a number or an object by mistake
    text = str(text)
    # truncate text if it is too long, this might mess up some displays like the adafruit 2 line char lcd
    text = '{:.{width}}'.format(text, width = display_char)
    # center and pad the string to the width specified
    text = '{:^{width}}'.format(text, width= display_char)
    return text


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
            current = unit.get_current_track_info()

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


def get_cpu_temp():
    cpu = gpiozero.CPUTemperature()
    return cpu.temperature

def get_outside_temp(city_key = "5913490", api_key="1b2c8e00bfa16ce7a48f76c3570fd3a2"):

    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = base_url + "id=" + city_key  +"&appid=" + api_key
    response = requests.get(complete_url)
    x = response.json()
    # print(x)
    y = x["main"]
    current_temperature = round(y["temp"] - 273)
    print("Current Temperature is:", str(current_temperature))
    return(str(current_temperature))


def make_pageset_tracklist(page_set = "0000", unit = "Portable", unit_ip = "192.168.1.35"):
    '''
    Opens json configuration file, gets the specified page set, and makes a list of dictionaries with the information
    from each track needed to play them, display track info, and make labels, etc.

    :param page_set:        The RFID tag number of the desired wallbox page set - usually from the rfid reader
    :type page_set:         str
    :param unit:            The name of the sonos unit to use.  currently not used
    :type unit:             str
    :param unit_ip:         The ip of the sonos unit, in case we can't find it by name.  currently not used
    :type unit_ip:          str
    :return:                A list of the tracks in the page set, each list item is a dictionary with
                            position, wallbox letter&number, song title, artist, source, didl item that can
                            be played
    :rtype:                 list
    '''

    wallbox_tracks = []
    # get a sonos unit.  We can use any sonos unit for this, the all have duplicate favorites, playlist info
    # we don't care which one we use
    active_unit = soco.discovery.any_soco()
    # try:
    #     active_unit = soco.discovery.by_name(unit)
    #     #if this fails then get unit by ip
    # except:
    #     active_unit = soco.SoCo(unit_ip)
    # get current page set from json file
    json = JsonComment()
    # allows use of python style comments in json file
    json_file = open("wallbox_pages.json", "r")
    # parse and load into python object (nested dictionary & list)
    page_sets = json.load(json_file)
    # get current page set as read from rfid tag passed as parameter into def
    page_set = page_sets[page_set]
    # initialize wallbox_selection number
    # loop through sections in page_set
    for section in page_set['sections']:
        # calculate number of selections in section
        num_selections = int(section['end']) - int(section['start']) + 1
        type = section['type']
        page_set_item_number = int(section['start'])

        if type == "sonos_favorites" or type == 'sonos_playlists':
            start = int(section['start_list'])
            # if type == 'sonos_playlists':
            #     tracks = sonos_unit.music_library.get_music_library_information('sonos_playlists')[5].tracklist
            #     print(tracks)
            for selection in range(num_selections):
                track = self.active_unit.music_library.get_music_library_information(type)[start + selection]
                page_set_item_number += 1
                if type == 'sonos_favorites':
                    page_set_item = {'title': track.reference.title, "song_title": track.reference.title,
                                     'artist': '',
                                     'source': track.description, 'type': type, 'ddl_item': track.reference}
                elif type == 'sonos_playlists':
                    page_set_item = {'title': track.title, "song_title": track.title, 'artist': '',
                                     'source': "Sonos Playlist", 'type': type,
                                     'ddl_item': track, 'playmode': section['play_mode']}
                # add to page_set_items list
                self.wallbox_tracks.insert(page_set_item_number, page_set_item)

        elif type == "sonos_playlist_tracks":
            playlist = active_unit.get_sonos_playlist_by_attr("title", section['playlist_name'])
            # get the tracks for the playlist we found
            # playlist should only be 200 tracks long but get up to 300 in case there are extra tracks
            tracks = active_unit.music_library.browse(playlist, max_items=300)

            for selection in tracks:
                page_set_item_number += 1
                track = selection

                page_set_item = {'title': track.title, 'song_title': track.title, 'artist': track.creator,
                                 'source': track.album, 'type': type, 'ddl_item': track}
                wallbox_tracks.insert(page_set_item_number, page_set_item)

    return wallbox_tracks




import math
import time
import soco
import gpiozero
import requests
import json

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





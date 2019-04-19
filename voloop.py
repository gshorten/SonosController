# Sonos volume control program
# Controls volume for selected Sonos unit, pauses and plays, and displays currently playing track

import soco
import time
import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD

# set pin mode on pi
GPIO.setmode(GPIO.BCM)


# function to get a sonos unit by it's name
# there is supposed to be a soco function for this but it missing from the package!
# def by_name(name):
#     devices = soco.discovery()
#     for device in devices:
#         if device.player_name == name:
#             break
#     return device


# ******************** TURN ENCODER BUTTON LIGHT ON, TO A SPECIFIC COLOUR *****************
# setup GPIO pins for LEDs on the encoder pushbutton
GPIO.setup(22, GPIO.OUT)
GPIO.output(22, GPIO.HIGH)
GPIO.setup(27, GPIO.OUT)
GPIO.output(27, GPIO.HIGH)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.HIGH)


def encoder_light(on_off, colour='none'):
    # turns green light on the encoder button (shows vol control unit is on)
    if on_off == 'off':
        GPIO.output(22, GPIO.HIGH)
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(17, GPIO.HIGH)
        return
    if on_off == 'on':
        if colour == 'green':
            pin = 22
        elif colour == 'red':
            pin = 27
        elif colour == 'blue':
            pin = 17
        GPIO.output(pin, GPIO.LOW)
        return


# ******************* SET ENCODER BUTTON TO RED OR GREEN DEPENDING ON PLAYSTATE ***************

def button_colour(unit):
    # changes colour of light on encoder button depending on play state
    unit_state = unit.get_current_transport_info()
    time.sleep(.1)  # pause long enough for sonos to respond
    playstate = unit_state['current_transport_state']
    if playstate == "PAUSED_PLAYBACK" or playstate == "STOPPED":
        encoder_light('off', 'green')
        encoder_light('on', 'red')
    elif playstate == "PLAYING":
        encoder_light('off', 'red')
        encoder_light('on', 'green')
    return


# *****************************    DISPLAY STUFF ON LCD DISPLAY ****************************************
# Initialize the LCD
lcd = LCD.Adafruit_CharLCDPlate()


def lcd_display(line1, line2='nothing', duration=0):
    # displays two lines of text, sets display time out timer, turns on backlight
    # if second line is 'nothing' replace with 16 spaces !
    if is_ascii(line1) and is_ascii(line2):
        global display_timer  # this is the timer for the lcd backlight tiifmeout (it's really bright!)
        lcd.set_backlight(.25)  # turn on the lcd backlight
        # lcd.set_color(0,1,0)
        display_timer = time.time()  # save time we put a message on the LCD, we use this later to timeout the lcd
        lcd.clear()  # clear whatever was on there before
        if len(line1) > 16:
            line1 = line1[:15]
        if len(line2) > 16:
            line2 = line2[:15]
        line1 = center_text(line1)
        line2 = center_text(line2)
        if line2 == 'nothing':
            line2 = "----------------"  # replace "nothing" keyword with 16 spaces (so lcd does not display garbage)

        text = str(line1) + '\n' + str(
            line2)  # make sure the two lines are strings, concatenate them, split to two lines
        lcd.message(text)
        # display on the LCD
        if duration > 0:
            time.sleep(duration)
        return

    else:
        lcd.message("")
        return


def is_ascii(text):
    # checks to see if string is a valid ascii
    isascii = lambda text: len(text) == len(text.encode())
    return isascii


def center_text(text):
    # centers text within 16 character length of the display
    text_length = len(text)
    padding = int(round((16 - text_length) / 2, 0))
    padding_text = " " * padding
    display_text = padding_text + text + padding_text
    return display_text


# ****************** GET THE TITLE AND ARTIST FOR THE CURRENTLY PLAYING TRACK ***************

def is_siriusxm(current_track):
    # tests to see if the current track is a siriusxm station
    s_title = current_track['title']
    s_title = s_title[0:7]

    if s_title == 'x-sonos':
        # only siriusxm stations seem to start this way
        return True
    else:
        return False


def siriusxm_track_info(current_track):
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

    if title[0:9] == 'device.asp':  # some radio stations first report this as title, filter it out until title appears
        track_info['xm_title'] = "    "
        track_info['xm_artist'] = "   "
    else:
        track_info['xm_title'] = title
        track_info['xm_artist'] = artist

    return track_info


def current_track_info(sonos_unit):
    # returns a dictionary "currently_playing" with "title" and "from" (ie, station, artist) for the currently playing track
    # this is used to update the display, such as after adding a track to the queue or pausing / playing
    currently_playing = {'title': "", 'from': "", 'meta': ''}  # dictionary to store track information
    current_track = sonos_unit.get_current_track_info()
    time.sleep(.1)  # pause long enough to get track info
    try:
        if is_siriusxm(current_track):
            # check to see if it is a siriusxm source, if so, then get title and artist using siriusxm_track_info function
            current = siriusxm_track_info(current_track)
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


# **************** DISPLAY CURRENT TITLE AND ARTIST ON LCD *************************

def display_currently_playing(sonos_unit, dur=1):
    # displays current title and artist on lcd
    try:
        current = current_track_info(sonos_unit)
        time.sleep(.05)
        lcd_display(current['title'], current['from'], dur)
    except:
        return


# ************************* DISPLAY ZONE NAME, NUMBER, AND VOLUME LEVEL OF ZONE ***********
def display_unit_info(unit, dur=0):
    try:
        unit_vol = unit.volume
        time.sleep(.1)
        name_display = str(unit_names[unit_index])
        unit_no = str(unit_index + 1) + ' of ' + str(no_of_units) + ' Vol:' + str(unit_vol)
        lcd_display(name_display, unit_no, duration=dur)
        return
    except:
        return


# **************************  SELECT SONOS UNIT *********************************************
# HAVE TO COMMENT THIS ALL OUT BECAUSE soco.SoCo.discovery() IS BROKEN, DON'T KNOW WHY!!!

# pushbutton cycles through units and sets one to be the target of volume, mute, etc
#
# select_button = 13
# GPIO.setup(select_button, GPIO.IN)  # pull this switch up with 2.7k resitor to 3.3v
# # units = soco.discovery.discover()  # get list of all the soco units
#
# # commented out because for some reason this makes the program crash when started from rc.local on startup
# # but it works fine when I start the program from the command line !@#
# # with open("lastunit.txt") as saved_unit:
# #     global unit_index
# #     unit_str = saved_unit.read()
# #     unit_index = int(unit_str,10) - 1
#
# unit_index = 0
# # no_of_units = len(units)
# time_since_last_push = time.time()
# # unit_names = []
# name_display = ''


# def select_unit(cb):
#     # when select button is pushed display name of unit and select it as unit for volume control, displaying track, etc.
#     # first push just displays current unit (last one selected)
#     # if it's been less than 2 seconds since last push then this push increases the index to show next unit
#     print("Select Button Pushed ")
#     try:
#         global time_since_last_push, unit_selected, volume, previous_track, unit_index, unit
#
#         if time.time() - time_since_last_push >= 5 and unit_selected:
#             if playstate(unit) == 'PLAYING':
#                 time.sleep(.05)
#                 display_unit_info(unit, 4)
#                 display_currently_playing(unit, 3)
#                 lcd_display(time(), "", 4)
#                 # previous_track = current_track_info(unit)['meta']
#             else:
#                 display_unit_info(unit, 2)
#
#             previous_track = current_track_info(unit)['meta']
#             time_since_last_push = time.time()
#             return

        # else:
        # print("selecting unit now")
        # # if this push is within x seconds of the last push then
        # unit_index += 1  # go to next sonos unit
        # if unit_index >= no_of_units:
        #     unit_index = 0
        #
        # unit = soco.discovery.by_name(unit_names[unit_index])
        # volume = unit.volume
        # time.sleep(.05)
        # display_unit_info(unit, 1)
        # button_colour(unit)
        # unit_selected = True
        # time_since_last_push = time.time()  # unless we are at end of list, then start from 0 again
        #
        # # write unit name to a file so we can start with that one next time program starts
        # # commented out because for some reason this makes the program crash when started from rc.local on startup
        # # but it works fine when I start the program from the command line !@#
        # with open("lastunit.txt","w+") as saved_unit:
        #     unit_str = str(unit_index)
        #     saved_unit.write(unit_str)
        #
        # print(unit_no,name_display,' at ',unit.ip_address)
        # print('Group Coordinator:', unit.group.coordinator)
        # print('Group Members:', unit.group.members)
        # print('------------------------------------')

#     except:
#         return
#
#
# GPIO.add_event_detect(select_button, GPIO.FALLING, callback=select_unit, bouncetime=500)

# ****************************** GET NEW VOLUME SETTING FROM ENCODER ***********************************

# enc_a = 19
# enc_b = 26
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(enc_a, GPIO.IN)  # define the Encoder switch inputs
# GPIO.setup(enc_b, GPIO.IN)
# Encoder_A_old = 0
# Encoder_B_old = 0
# volume_changed = False
# error = 0
# debounce = 1
#
#
# def volume_set(cb):
#     global Encoder_A_old, Encoder_B_old, error, volume, volume_changed, volume_time
#     print('Current Volume: ', volume)
#
#     Encoder_A, Encoder_B = GPIO.input(enc_a), GPIO.input(enc_b)
#
#     if ((Encoder_A, Encoder_B_old) == (1, 0)) or ((Encoder_A, Encoder_B_old) == (0, 1)):
#         # this will be clockwise rotation
#         volume += 1
#         if volume >= 100: volume = 100
#
#     elif ((Encoder_A, Encoder_B_old) == (1, 1)) or ((Encoder_A, Encoder_B_old) == (0, 0)):
#         # this will be counter-clockwise rotation
#         volume -= 1
#         if volume < 0:
#             volume = 0
#     else:
#         # this will be an error
#         error += 1
#         print('Error count is ', error)
#
#     Encoder_A_old, Encoder_B_old = Encoder_A, Encoder_B
#     volume_time = time.time()
#     volume_changed = True
#     print('New Volume: ', volume)
#
# GPIO.add_event_detect(enc_a, GPIO.BOTH, callback=volume_set, bouncetime=debounce)    # Encoder A
# GPIO.add_event_detect(enc_b, GPIO.BOTH, callback=volume_set, bouncetime=debounce)   # Encoder B

class VolumeControl:
    # class for the volume control rotary encoder
    # debounce = 150
    # debounce for the rotary encoder
    # error = 0
    # initialize the old values for the encoder
    encoder_b_old = 0
    encoder_a_old = 0
    volume_changed = False

    def __init__(self,enc_a,enc_b,s_unit):
        self.unit = s_unit
        # assign the GPIO pins to variables
        # enc_a is gpio 19, enc_b is gpio 26
        self.enc_a = enc_a
        self.enc_b = enc_b
        self.debounce = 25
        self.counter = 0
        self.channel_list = []
        # list to store the callback channels as they occur
        GPIO.setmode(GPIO.BCM)
        # define the Encoder switch inputs
        GPIO.setup(self.enc_a, GPIO.IN)
        GPIO.setup(self.enc_b, GPIO.IN)
        # get the value of the encoder and assign it to variables
        self.count = 0

        # set up the callback function
        GPIO.add_event_detect(self.enc_a, GPIO.FALLING, callback=self.volume_set, bouncetime=self.debounce)  # Encoder A
        GPIO.add_event_detect(self.enc_b, GPIO.FALLING, callback=self.volume_set, bouncetime=self.debounce)  # Encoder B

    def volume_set(self,channel):
        encoder_a, encoder_b = GPIO.input(self.enc_a), GPIO.input(self.enc_b)

        # sets the volume
        # get volume of the current unit
        unit_volume = self.unit.volume
        # print('Current Volume: ', unit_volume)
        # print("Time: ", time.time())
        print("spin number:",self.count)
        print('Channel: ',channel)
        print("a:",encoder_a)
        print("b:",encoder_b)

        self.channel_list.append(channel)
        self.counter += 1
        if len(self.channel_list) ==2:
            volume_channel = self.channel_list[-2]
            self.channel_list = []
            print("volume_channel: ",volume_channel)
        time.sleep(.1)

        # print("encoder a, encoder b: ", encoder_a, encoder_b)
        #  = str(encoder_a) + str(encoder_b) + str(self.encoder_a_old) + str(self.encoder_b_old)
        # (spin_binary)
        # spin_decimal = int(spin_binary,2)
        # print (spin_decimal)
        # if (encoder_a,self.encoder_b_old) == (1, 0) or (encoder_a, self.encoder_b_old) == (0,1):
        # if (encoder_b, self.encoder_a_old) == (1, 0):
        #     # this will be clockwise rotation
        #     unit_volume += 1
        #     if unit_volume >= 100: unit_volume = 100
        #
        # elif (encoder_a,self.encoder_b_old) == (1, 0):
        #     # this will be counter-clockwise rotation
        #     unit_volume -= 1
        #     if unit_volume < 0:
        #         unit_volume = 0
        # else:
        #     # this will be an error
        #     self.error += 1
        #     print('Error count is ', self.error)
        # print("New Volume: ", unit_volume)
        # unit.volume = unit_volume
        self.count += 1

        self.encoder_b_old = encoder_b
        self.encoder_a_old = encoder_a
        # print('New Volume: ', unit_volume)

def playstate(unit):
    try:
        unit_state = unit.get_current_transport_info()
        time.sleep(.2)
        playstate = unit_state['current_transport_state']
        return playstate
    except:
        return


# **********************  PAUSE / PLAY - ENCODER PUSHBUTTON *************************
# pauses and un pauses play

enc_play_pause = 4  # GPIO port for play / pause button on encoder
GPIO.setup(enc_play_pause, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


# setup pin for the encoder pushbutton

def encoder_button(button):
    try:
        print('encoder button pressed')
        global unit
        name = unit.player_name
        unit_status = playstate(unit)
        time.sleep(.5)

        if unit_status == "PAUSED_PLAYBACK" or unit_status == "STOPPED":
            unit.play()
            time.sleep(.1)  # seems like we have to give unit time to respond
            # print('not ',playstate)
            encoder_light('on', 'green')
            encoder_light('off', 'red')
            lcd_display('    Playing   ', name, 5)
            display_currently_playing(unit, 5)
            # lcd_display(time(), "", 5)

        elif unit_status == "PLAYING":
            unit.pause()
            time.sleep(.1)
            # print('not ',playstate[unit])
            encoder_light('off', 'green')
            encoder_light('on', 'red')
            lcd_display('     Paused     ', name, 2)
            lcd.set_backlight(0)
        return
    except:
        return


GPIO.add_event_detect(enc_play_pause, GPIO.RISING, callback=encoder_button, bouncetime=1000)


# seems like we need a huge debounce on this button :-(

def set_wifi():
    # set up a dictionary to store wifi settings
    # should probably change this to read from a config file.
    return


# *****************************  MAIN PROGRAM LOOP ***********************************************

vol_check = time.time()
display_timer = time.time  # timer for display time out
lcd_timeout = 15
unit_selected = True

lcd.set_backlight(.25)  # set lcd backlight to 25% brightness
lcd.set_color(0, 1, 0)  # set lcd backlight to blue
lcd.clear()
lcd_display('Sonos Remote Volume', '    Control     ', 2)
wifi_selected = True
#unit = soco.SoCo('192.168.0.16')       # garage
unit = soco.SoCo('192.168.0.21')        # portable
unit_volume_set = VolumeControl(19,26,unit)

# while not wifi_selected:
#     # before doing anything else, we select the wifi system
#     wifi_selected = True  # just skip this for now until I figure out how to do it
#
# # set default sonos unit
#
#
#
# # instead of selecting random unit start with the garage
# # unit = by_name("Garage")
# print(unit.player_name)
# button_colour(unit)
# previous_track = current_track_info(unit)['meta']
# volume = unit.volume
# old_volume = volume
# volume_time = time.time()
# old_status = playstate(unit)
#
# # make a list of the names of all the sonos units in the system and put them in a list "unit.name"
# # for (index, item) in enumerate(units):
# #     unit_names.append(item.player_name)
# #     print(unit_names[index])
#
# lcd_display('Connected To', 'Garage')
# while not unit_selected:
#     # wait until user selects a unit - ie, pushes the zone select button
#     pass
#
while True:
    try:
        pass

             # change the volume
#         # while volume_changed:
#         #     # while the volume changed flag is true (set in def set_volume)
#         #     # loop, check to see if the volume has has changed (volume set in def set_volume)
#         #
#         #     unit.volume = volume  # set current unit volume
#         #     time.sleep(.05)
#         #     if old_volume != volume:
#         #         lcd_display("Volume", str(volume))  # display new volume only if it has changed
#         #     time.sleep(.1)
#         #     print('I changed the volume to:', volume)
#         #     if time.time() - volume_time > 3:
#         #         # if it is more than 2 seconds since the volume was last changed then display
#         #         # unit info and currently playing info
#         #         display_unit_info(unit, 1.5)
#         #         display_currently_playing(unit, 2)
#         #         volume_changed = False  # reset volume change flag
#         #     old_volume = volume
#
#         # Update display - if it has changed
#         track_info = current_track_info(unit)
#         time.sleep(.05)
#
#         if track_info['meta'] != previous_track and playstate(
#                 unit) == 'PLAYING' and time.time() - time_since_last_push > 6:
#             display_currently_playing(unit)
#             previous_track = track_info['meta']
#
#         # timeout display to save battery
#         if time.time() - display_timer >= lcd_timeout:
#             lcd.set_backlight(0)
#
#         # update play status of button
#         unit_status = playstate(unit)
#         time.sleep(.05)
#         if old_status != unit_status:
#             if unit_status == "PAUSED_PLAYBACK" or unit_status == "STOPPED":
#                 encoder_light('off')
#                 encoder_light('on', 'red')
#             elif unit_status == "PLAYING":
#                 encoder_light('off')
#                 encoder_light('on', 'green')
#             old_status = unit_status
    except KeyboardInterrupt:
        lcd.clear()
        lcd.set_backlight(0)
        GPIO.cleanup()  # clean up GPIO on CTRL+C exit
#
# # TO DO
# # detect if current zone is master or not... can only pause/play master

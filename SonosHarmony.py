#!/usr/bin/env python
'''
Module for controlling the Logitech Harmony hubs / remotes from my Sonos wallbox controllers
muchas gracias to EScape 2018 and others for figuring this all out
'''

import harmony

class HarmonyHubDevice(harmony.harmonysock):
    '''
    Great Room Logitech Harmony hub
    subclass of harmony.py
    pass instance of this class into SonosVolControl in SonosControl, use volume control on wallbox controller to
    change TV volume when it's not being used for controlling the volume of the sonos system.
    '''


    def __init__(self, ip = '192.168.1.55',rport = '14255516', device = '60692019'):
        '''
        :param ip:      ip address of the harmony hub
        :type ip:       str
        :param rport:   remote port of the harmony device, note NOT the "port" - its "remoteId"
        :type rport:    str
        :param device:  the harmony number of the device.  On my system 60692019 is the Onkyo reciever
        :type device:   str
        '''
        self.device = device
        harmony.harmonysock.__init__(self,host = ip,hubid = rport)

    def volume_up(self):
        '''
        turns the volume up on the selected device, one increment....have no idea how much this is but on tv shows
        one number up.
        :return:
        :rtype:
        '''

        self.sendkey(self.device,key="VolumeUp")

    def volume_down(self):
        '''
        turns volume down
        :return:
        :rtype:
        '''
        self.sendkey(self.device,key="VolumeDown")

    def Mute(self):
        '''
        Mutes audio.  turning volume up or down unmutes.
        :return:
        :rtype:
        '''
        self.sendkey(self.device, key="Mute")


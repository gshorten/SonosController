from __future__ import print_function
import logging
logging.basicConfig()
import soco
from pprint import pprint
from soco import events_twisted
soco.config.EVENTS_MODULE = events_twisted
from twisted.internet import reactor
import time
import SonosUtils

class SonosTrackUpdater:
    """
    Calls a callback method when the playstate or track changes for the active sonos unit
    """

    def __init__(self,active_unit):

        self.device = active_unit
        reactor.callWhenRunning(self.main)
        reactor.run()

    def new_track_info(self,event):
        try:
            meta = event.variables['current_track_meta_data']
            transport_state = event.variables['transport_state']
            track_info = SonosUtils.getTitleArtist(unit=self.device)
            print()
            print('*************** Changed *************')
            print('          ', time.asctime())
            print('Meta: ', meta)
            print('Transport State: ',transport_state)
            print('Track Info: ', track_info['track_title'],"  ",track_info['track_from'])
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
        sub2.callback = self.updateDisplays
        def before_shutdown():
            # sub.unsubscribe()
            sub2.unsubscribe()
            soco.events_twisted.event_listener.stop()
        reactor.addSystemEventTrigger(
            'before', 'shutdown', before_shutdown)


Update = UpdateDisplay('Portable')


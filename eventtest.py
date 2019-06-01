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
            self.track_info = SonosUtils.getTitleArtist(unit=self.device)
            print()
            print('*************** Changed *************')
            print('          ', time.asctime())
            print('Meta: ', self.meta)
            print('Transport State: ',self.transport_state)
            print('Track Info: ', self.track_info['track_title'],"  ",self.track_info['track_from'])
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

    if __name__=='__main__':
        reactor.callWhenRunning(Update.main)
        reactor.run()

Update = UpdateDisplay('Portable')


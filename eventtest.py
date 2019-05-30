from __future__ import print_function
import logging
logging.basicConfig()
import soco
from pprint import pprint
import twisted
#
from soco import events_twisted
soco.config.EVENTS_MODULE = events_twisted
from twisted.internet import reactor

def print_event(event):
    try:
        pprint (event.variables)
    except Exception as e:
        pprint ('There was an error in print_event:', e)
def main():
    # pick a device at random and use it to get
    # the group coordinator
    # device = soco.discover().pop().group.coordinator
    device = soco.discovery.by_name("Portable")
    print (device.player_name)
    sub = device.renderingControl.subscribe().subscription
    sub2 = device.avTransport.subscribe().subscription
    sub.callback = print_event
    sub2.callback = print_event
    def before_shutdown():
        sub.unsubscribe()
        sub2.unsubscribe()
        soco.events_twisted.event_listener.stop()
    reactor.addSystemEventTrigger(
        'before', 'shutdown', before_shutdown)
if __name__=='__main__':
    reactor.callWhenRunning(main)
    reactor.run()
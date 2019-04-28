# testing soco events classes

from __future__ import print_function
try:
    from queue import Empty
except:  # Py2.7
    from Queue import Empty

import soco
from pprint import pprint
from soco.events import event_listener
# pick a device at random
# device = soco.discover().pop()
# print(device.player_name)
device = soco.discovery.by_name('Portable')
sub = device.renderingControl.subscribe()
sub2 = device.avTransport.subscribe()

while True:
    try:
        event = sub.events.get(timeout=0.5)
        print('************* RenderingControl*************')
        pprint (event.variables)

    except Empty:
        pass
    try:
        event = sub2.events.get(timeout=0.5)
        print("************** avTransport *****************")
        pprint (event.variables)
    except Empty:
        pass

    except KeyboardInterrupt:
        print()
        print('unsubscribing')
        sub.unsubscribe()
        sub2.unsubscribe()
        event_listener.stop()
        break

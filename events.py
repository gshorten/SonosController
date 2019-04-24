from __future__ import print_function
try:
    from queue import Empty
except:  # Py2.7
    from Queue import Empty

import soco
from pprint import pprint
from soco.events import event_listener
# pick a device at random
device = soco.discover.by_name('Portable')
print (device.player_name)
sub = device.renderingControl.subscribe()
sub2 = device.avTransport.subscribe()

while True:
    try:
        event = sub.events.get(timeout=0.5)
        pprint (event.variables)
        pprint()
    except Empty:
        pass
    try:
        event = sub2.events.get(timeout=0.5)
        pprint (event.variables)
        pprint()
    except Empty:
        pass

    except KeyboardInterrupt:
        sub.unsubscribe()
        sub2.unsubscribe()
        event_listener.stop()
        break
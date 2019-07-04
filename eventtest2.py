try:
    from queue import Empty
except:  # Py2.7
    from Queue import Empty

import soco
from soco.events import event_listener
import logging
logging.basicConfig(level=logging.DEBUG)
# pick a device
active = soco.discovery.by_name('Portable')
# Subscribe to ZGT events
sub = active.zoneGroupTopology.subscribe()

# print out the events as they arise
while True:
    try:
        event = sub.events.get(timeout=0.5)
        print(event)
        print(event.sid)
        print(event.seq)

    except Empty:
        pass
    except KeyboardInterrupt:
        sub.unsubscribe()
        event_listener.stop()
        break

import soco
from pprint import pprint
from soco.events import event_listener
# pick a device at random
device = soco.discovery.by_name("Garage")
print (device.player_name)
sub = device.renderingControl.subscribe()
sub2 = device.avTransport.subscribe()

while True:
    try:
        try:
            event = sub.events.get(timeout=0.5)
            pprint ("RenderingControl Events: ", event.variables)
            print("******************************************")
        except:
            pass
        try:
            event = sub2.events.get(timeout=0.5)
            pprint ("avTransport Events: ", event.variables)
            print("******************************************")
        except :
            pass

    except KeyboardInterrupt:
        sub.unsubscribe()
        sub2.unsubscribe()
        event_listener.stop()
        break
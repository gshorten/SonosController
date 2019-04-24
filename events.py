
import soco

from soco.events import event_listener

print ("Events listener test")
device = soco.SoCo('192.168.1.21')
print (soco.SoCo.player_name)
sub = device.renderingControl.subscribe()
sub2 = device.avTransport.subscribe()

while True:
    try:
        try:
            event = sub.events.get(timeout=0.5)
            print (event.variables)
            print()
        except:
            pass
        try:
            event = sub2.events.get(timeout=0.5)
            print (event.variables)
            print ()
        except:
            pass

    except KeyboardInterrupt:
        sub.unsubscribe()
        sub2.unsubscribe()
        event_listener.stop()
        break
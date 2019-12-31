
import pyudev

context = pyudev.Context()
usb_thing = pyudev.Devices.from_device_file(context,'/dev/ttyUSB0')
print(usb_thing)

monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('block')

def usb_event(action, device):
    print(action, device)

observer = pyudev.MonitorObserver(monitor, usb_event)
observer.daemon = False
observer.start()

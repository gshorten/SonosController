
import pyudev

context = pyudev.Context()
usb_thing = pyudev.Devices.from_device_file(context,'/dev/ttyUSB0')
print(usb_thing)
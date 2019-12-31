'''
Rfid reader test, triggering on usb event
'''

import time
import serial
# import GLib
from pyudev import Context, Monitor
from pyudev.glib import MonitorObserver

# Create a device database connection
context = Context()

# Create a synchronous device event monitor
monitor = Monitor.from_netlink(context)

# Optional: apply a filter for the desired hardware
monitor.filter_by(subsystem='usb')

# Create a asynchronous observer for device events
observer = MonitorObserver(monitor)

# Connect the observer to a method of your choosing (in this case device_event())
observer.connect('device-event', device_event)

# Start the monitor
monitor.start()

# Run an endless loop to monitor events
# GLib.MainLoop().run()

def device_event(observer, device):
    if device.action.decode("string-escape") == "add":
        print ('device attached. do some work.', device)
    elif device.action.decode("string-escape") == "remove":
        print ('device removed. do some work.', device)

while True:
    time.sleep(.1)

# port = "/dev/ttyUSB0"
# reader = serial.Serial('/dev/ttyUSB0',9600)
# reader.flushInput()
# reader.flushOutput()
# while True:
#     try:
#         taginfo = reader.read()
#         print("tag info:",taginfo)
#         time.sleep(.5)
#         # eader.serialPort.flushInput()
#     except Exception as e:
#         print("error reading tag:",e)
#     # reader.flushInput()
"""
OLED display test
"""
import OLEDDisplay
import time

Display = OLEDDisplay.OLED()

while True:
    # Display.clear_display()
    ti = time.gmtime()
    line1 = " The time is:"
    line2 = time.asctime(ti)
    Display.display_text(line1, line2)
    time.sleep(3)
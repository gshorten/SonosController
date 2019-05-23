"""
OLED display test
"""
import OLEDDisplay
import time

Display = OLEDDisplay.OLED()

while True:
    # Display.clear_display()

    line1 = " The time is:"
    line2 = time.ctime()
    Display.display_text(line1, line2)
    time.sleep(3)
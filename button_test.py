"""
test the button press
"""

import SonosHWTest
import i2cCharLCD
import time

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(duration):
    if duration is 'short':
        print('short press: ')
        print('-------------------------------')
    elif duration is 'long':
        print ('long press')
        print('-------------------------------')
    #ButtonLCD.display_text('Button Duration', button_type)
    #ButtonLCD.clear()


# little black button on front of volume control box; used to change sonos unit
Button = SonosHWTest.PushButton(button_pin=18, long_press=1000, callback=button_test, gpio_up_down='up',
                                      debounce=50)


while True:
    time.sleep(10)
    pass
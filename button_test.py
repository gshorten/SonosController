"""
test the button press
"""

import SonosHWTest
import i2cCharLCD
import time

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(short):
    if short:
        print('Single: ', short)
        print('-------------------------------')
    elif not short:
        print ('Double: ', short)
        print('-------------------------------')
    #ButtonLCD.display_text('Button Duration', button_type)
    #ButtonLCD.clear()

# little black button on front of volume control box; used to change sonos unit
Button = SonosHWTest.PushButton(button_pin=18, double=.5, callback=button_test, gpio_up_down='up',
                                      debounce=1)


while True:
    time.sleep(10)
    pass
"""
test the button press
"""

import SonosHWTest
import i2cCharLCD
import time

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(double):
    if double:
        print('double press: ', double)
        print('-------------------------------')
    elif not double:
        print ('single press, double is: ', double)
        print('-------------------------------')
    #ButtonLCD.display_text('Button Duration', button_type)
    #ButtonLCD.clear()


# little black button on front of volume control box; used to change sonos unit
Button = SonosHWTest.PushButton(button_pin=18, double_press=.5, callback=button_test, gpio_up_down='up',
                                      debounce=100)


while True:
    time.sleep(10)
    pass
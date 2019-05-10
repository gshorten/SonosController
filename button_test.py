"""
test the button press
"""

import SonosHWTest
import i2cCharLCD
import time

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(double_press):
    if double_press:
        print('double press: ', double_press)
        print('-------------------------------')
    elif not double_press:
        print ('single press, double is: ', double_press)
        print('-------------------------------')
    #ButtonLCD.display_text('Button Duration', button_type)
    #ButtonLCD.clear()


# little black button on front of volume control box; used to change sonos unit
Button = SonosHWTest.PushButton(button_pin=18, double_press=.5, callback=button_test, gpio_up_down='up',
                                      debounce=200)


while True:
    time.sleep(10)
    pass
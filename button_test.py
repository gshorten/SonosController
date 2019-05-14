"""
test the button press
"""

import SonosHW
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
    ButtonLCD.clear()
    ButtonLCD.display_text('Button Duration', duration)


# little black button on front of volume control box; used to change sonos unit
BlackButton = SonosHW.PushButton(button_pin=18, long_press=.75, callback=button_test, gpio_up_down='up',
                                      debounce=50)
VolumeButton = SonosHW.PushButton(button_pin=12, long_press=.75, callback=button_test,
                                  gpio_up_down='down', debounce = 50)


while True:
    time.sleep(30)
    pass
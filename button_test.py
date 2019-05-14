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
        print('-------------------------------')
    elif duration is 'long':
        print('-------------------------------')
    ButtonLCD.clear()
    ButtonLCD.display_text('Button Duration', duration)


# little black button on front of volume control box; used to change sonos unit
BlackButton = SonosHW.PushButton(button_pin=18, long_press=1, callback=button_test, gpio_up_down='up',
                                      debounce=25)
VolumeButton = SonosHW.PushButton(button_pin=12, long_press=1, callback=button_test,
                                  gpio_up_down='down', debounce = 20)


while True:
    time.sleep(30)
    pass
"""
test the button press
"""

import SonosHW


def button_test(button_type):
    if button_type == 'short':
        print('Length: ', button_type)
        print('-------------------------------')
    elif button_type == 'long':
        print ('Length: ', button_type)
        print('-------------------------------')


# little black button on front of volume control box; used to change sonos unit
Button = SonosHW.PushButton(button_pin=18, short=1, callback=button_test, gpio_up_down='up',
                                      debounce=10)


while True:
    pass
"""
test the button press
"""

import SonosHW
import i2cCharLCD

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(button_type):
    if button_type == 'short':
        print('Length: ', button_type)
        print('-------------------------------')
    elif button_type == 'long':
        print ('Length: ', button_type)
        print('-------------------------------')
    ButtonLCD.display_text('Button Duration', button_type)

# little black button on front of volume control box; used to change sonos unit
Button = SonosHW.PushButton(button_pin=18, short=1, callback=button_test, gpio_up_down='up',
                                      debounce=50)


while True:
    pass
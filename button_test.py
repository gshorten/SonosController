"""
test the button press
"""

import SonosHWTest
import SonosHW
import i2cCharLCD
import time
import datetime

# LCD on the wallbox
ButtonLCD = i2cCharLCD.ExtendedAdafruitI2LCD()

def button_test(duration):
    if duration is 'short':
        print('-------------------------------')
    elif duration is 'long':
        print('-------------------------------')
    ButtonLCD.clear()
    ButtonLCD.display_text('Button Duration', duration)

def single_button_test():
    print("Button Pressed")
    ButtonLCD.clear()
    now = datetime.datetime.now()
    now = now.strftime("%H:%M:%S")
    ButtonLCD.display_text("Button Pressed", now, sleep=10)



# little black button on front of volume control box; used to change sonos unit
BlackButton = SonosHW.SinglePressButton(pin=18, callback=single_button_test, gpio_up = 1,
                                      debounce=500)
#VolumeButton = SonosHWTest.PushButton(button_pin=12, long_press=750, callback=button_test,
                                 # gpio_up_down='down', debounce = 20)


while True:
    time.sleep(30)
    pass
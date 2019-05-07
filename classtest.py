
"""
testing creating subclasses of adafruit i2c lcd modules
"""


import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c
import soco
import time


# the code below works

# lcd_columns = 16
# lcd_rows = 2
# i2c = busio.I2C(board.SCL, board.SDA)
# lcd = adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
#
# lcd.color = [100, 0, 0]
# lcd.message = "Hello\nCircuitPython"
# time.sleep(5)
# lcd.clear()
# lcd.color = [0,0,0]

#now try it with a class

# class TestLCD(adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C):
#
#     def __init__(self):
#         lcd_columns = 16
#         lcd_rows = 2
#         i2c = busio.I2C(board.SCL, board.SDA)
#         adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C.__init__(self,i2c,lcd_columns,lcd_rows)
#
#     def display_something(self, text = "", sleep=5):
#         self.color = (100,0,0)
#         self.message = text
#         self.message = "text"
#         time.sleep(sleep)
#         self.color = (0,0,0)
#         self.clear()
#
# test_lcd = TestLCD()
# test_lcd.display_something(text = "testing class", sleep=8)

class Unit:
    def __init__(self, default):
        self.default_name = default
        self.sonos_unit = ""
        self.sonos_name = ""

    def get_unit(self):
        self.sonos_unit = soco.discovery.by_name(self.default_name)
        self.sonos_name = self.sonos_unit.player_name


unit = Unit()
unit.get_unit()

print(unit.sonos_unit)
print(unit.sonos_name)


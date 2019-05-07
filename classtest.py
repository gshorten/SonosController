
"""
testing creating subclasses of adafruit i2c lcd modules
"""

# the code below works
import board
import busio

import adafruit_character_lcd.character_lcd_rgb_i2c
import time

lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
lcd = adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

lcd.color = [100, 0, 0]
lcd.message = "Hello\nCircuitPython"
time.sleep(5)
lcd.clear()
lcd.color = [0,0,0]



# now try it with a class

# class TestLCD(Character_LCD_RGB_I2C):
#
#     def __init__(self):
#         lcd_columns = 16
#         lcd_rows = 2
#         i2c = busio.I2C(board.SCL, board.SDA)
#         adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB.__init__()
#         adafruit_character_lcd.character_lcd_rgb_i2c.Character_LCD_RGB_I2C.__init__(self,i2c,lcd_columns,lcd_rows)
#
#
#     def display_something(self, text):
#         self.color = [100,0,0]
#         self.

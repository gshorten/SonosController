import board
import busio

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C
import time



lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
lcd = Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)


while True:
    try:
        lcd.color = [100,0,0]
        lcd.message = "Hello\nCircuitPython"
        #lcd.move_right()
        #lcd.blink = True
        time.sleep(2)
        lcd.clear()
        #lcd.color = [0,0,0]

    except KeyboardInterrupt:
        lcd.color = [0,0,0]
        lcd.clear()




import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as i2c_LCD
import time
#import adafruit_character_lcd.Character_LCD_RGB_I2C as character_lcd
#import adafruit_character_lcd.character_lcd_i2c as character_lcd


lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
lcd = i2c_LCD.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)
#lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns,lcd_rows)
#lcd = character_lcd.Character_LCD_Mono_I2C(i2c, lcd_columns, lcd_rows)

#lcd.color = [100, 0, 0]
#lcd.backlight = True
while True:
    try:
        lcd.color = [100,0,0]
        lcd.message = "Hello\nCircuitPython"
        #lcd.move_right()
        #lcd.blink = True
        time.sleep(.5)
        lcd.clear()
        #lcd.color = [0,0,0]

    except KeyboardInterrupt:
        lcd.color = [0,0,0]
        lcd.clear()




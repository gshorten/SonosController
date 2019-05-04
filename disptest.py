import board
import busio
import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd


lcd_columns = 16
lcd_rows = 2
i2c = busio.I2C(board.SCL, board.SDA)
#lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

lcd = character_lcd.Character_LCD_Mono_I2C(i2c, lcd_columns, lcd_rows)

#lcd.color = [100, 0, 0]
lcd.set_backlight(1)
lcd.message = "Hello\nCircuitPython"
while True:
    try:
        lcd.move_right()
    except KeyboardInterrupt:
        lcd.set_backlight(0)
        lcd.clear()




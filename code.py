# Quick test of TFT FeatherWing (ST7789) with Feather M0 or M4
# This will work even on a device running displayio
# Will fill the TFT black and put a red pixel in the center, wait 2 seconds,
# then fill the screen blue (with no pixel), wait 2 seconds, and repeat.

import time
import random
import digitalio
import board
import busio

from adafruit_rgb_display.rgb import color565
from adafruit_rgb_display import st7789

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.GP17)
dc_pin = digitalio.DigitalInOut(board.GP21)
reset_pin = digitalio.DigitalInOut(board.GP20)

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
print("Trying SPI lock")
while not spi.try_lock():
    pass
print("SPI lock succeeded")

# Create the ST7789 display:
display = st7789.ST7789(spi, cs=cs_pin, dc=dc_pin,
                        rst=reset_pin, baudrate=BAUDRATE)

# Main loop:
while True:
    print("foo")
    # Fill the screen red, green, blue, then black:
    for color in ((255, 0, 0), (0, 255, 0), (0, 0, 255)):
        display.fill(color565(color))
    # Clear the display
    display.fill(0)
    # Draw a red pixel in the center.
    display.pixel(display.width // 2, display.height // 2, color565(255, 0, 0))
    # Pause 2 seconds.
    time.sleep(2)
    # Clear the screen a random color
    display.fill(
        color565(random.randint(0, 255), random.randint(
            0, 255), random.randint(0, 255))
    )
    # Pause 2 seconds.
    time.sleep(2)

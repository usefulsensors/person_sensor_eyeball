# Spooky eyeball using a Person Sensor.
# Adapted from code by @todbot / Tod Kurt, original at
# https://github.com/todbot/circuitpython-tricks/.

import board
import busio
import digitalio
import displayio
import random
import struct
import time

import adafruit_imageload
from adafruit_st7789 import ST7789

last_person_sensor_time = 0


def get_faces(i2c):
    global last_person_sensor_time

    # The person sensor has the I2C ID of hex 62, or decimal 98.
    PERSON_SENSOR_I2C_ADDRESS = 0x62

    # We will be reading raw bytes over I2C, and we'll need to decode them into
    # data structures. These strings define the format used for the decoding, and
    # are derived from the layouts defined in the developer guide.
    PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
    PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
        PERSON_SENSOR_I2C_HEADER_FORMAT)

    PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
    PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

    PERSON_SENSOR_FACE_MAX = 4
    PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
        "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
    PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(
        PERSON_SENSOR_RESULT_FORMAT)

    # How long to pause between sensor polls.
    PERSON_SENSOR_DELAY = 0.3

    if time.monotonic() - last_person_sensor_time < PERSON_SENSOR_DELAY:
        return []
    last_person_sensor_time = time.monotonic()

    read_data = bytearray(PERSON_SENSOR_RESULT_BYTE_COUNT)
    i2c.readfrom_into(PERSON_SENSOR_I2C_ADDRESS, read_data)

    offset = 0
    (pad1, pad2, payload_bytes) = struct.unpack_from(
        PERSON_SENSOR_I2C_HEADER_FORMAT, read_data, offset)
    offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

    (num_faces) = struct.unpack_from("B", read_data, offset)
    num_faces = int(num_faces[0])
    offset = offset + 1

    faces = []
    for i in range(num_faces):
        (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
         is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_data, offset)
        offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
        face = {
            "box_confidence": box_confidence,
            "box_left": box_left,
            "box_top": box_top,
            "box_right": box_right,
            "box_bottom": box_bottom,
            "id_confidence": id_confidence,
            "id": id,
            "is_facing": is_facing,
        }
        faces.append(face)
    checksum = struct.unpack_from("H", read_data, offset)

    return faces


def map_range(s, a1, a2, b1, b2):
    return b1 + ((s - a1) * (b2 - b1) / (a2 - a1))


displayio.release_displays()

spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
while not spi.try_lock():
    pass
spi.configure(baudrate=24000000)  # Configure SPI for 24MHz
spi.unlock()

tft_cs = board.GP17
tft_dc = board.GP21
tft_reset = board.GP20

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_reset)

display = ST7789(display_bus, width=240, height=240, rowstart=80)

dw, dh = 240, 240  # display dimensions

# load our eye and iris bitmaps
eyeball_bitmap, eyeball_pal = adafruit_imageload.load("eye0_ball2.bmp")
iris_bitmap, iris_pal = adafruit_imageload.load("eye0_iris0.bmp")
iris_pal.make_transparent(0)

# compute or declare some useful info about the eyes
iris_w, iris_h = iris_bitmap.width, iris_bitmap.height  # iris is normally 110x110
iris_cx, iris_cy = dw//2 - iris_w//2, dh//2 - iris_h//2
r = 20  # allowable deviation from center for iris

main = displayio.Group()
display.show(main)
eyeball = displayio.TileGrid(eyeball_bitmap, pixel_shader=eyeball_pal)
iris = displayio.TileGrid(
    iris_bitmap, pixel_shader=iris_pal, x=iris_cx, y=iris_cy)
main.append(eyeball)
main.append(iris)
x, y = iris_cx, iris_cy
tx, ty = x, y
next_time = time.monotonic()
eye_speed = 0.25
twitch = 2

# The Pico doesn't support board.I2C(), so check before calling it. If it isn't
# present then we assume we're on a Pico and call an explicit function.
try:
    i2c = board.I2C()
except:
    i2c = busio.I2C(scl=board.GP5, sda=board.GP4)

# Wait until we can access the bus.
while not i2c.try_lock():
    pass

while True:
    faces = []
    faces = get_faces(i2c)
    facex, facey = None, None
    if len(faces) > 0:
        facex0 = (faces[0]['box_right'] - faces[0]
                  ['box_left']) // 2 + faces[0]['box_left']
        facey0 = (faces[0]['box_bottom'] - faces[0]
                  ['box_top']) // 2 + faces[0]['box_top']
        facex = map_range(facex0, 0, 255, 40, -40)
        facey = map_range(facey0, 0, 255, -40, 40)
        tx = iris_cx + facex
        ty = iris_cy + facey

    x = x * (1-eye_speed) + tx * eye_speed  # "easing"
    y = y * (1-eye_speed) + ty * eye_speed
    iris.x = int(x)
    iris.y = int(y)
    display.refresh()

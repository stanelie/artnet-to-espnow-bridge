Circuitpython on Waveshare ESP32-S3-ZERO

import espnow
import wifi
import board
import time
import neopixel

channel = 7

wifi.radio.start_ap(" ", "", channel=channel, max_connections=10)
wifi.radio.stop_ap()

e = espnow.ESPNow()

pixel_pin = board.NEOPIXEL
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))

def start_ap(channel):
    wifi.radio.start_ap(b'my_ap', b'password', channel=channel)

def check_for_packet():
    if e:
        return True
#     else:
#         False

while True:
    start_ap(channel)
    start_time = time.monotonic()
    while time.monotonic() - start_time < 1:
        if check_for_packet():
            print(f"Packet received on channel {channel}")
            packet = e.read()
            print(packet[1])
            dmx_data = packet[1]
            canal3 = dmx_data[2]
            pixels.fill((0,0,canal3))
            break
    else:
        # No packet received, stop AP and increment channel
        wifi.radio.stop_ap()
        channel = (channel % 11) + 1

# Circuitpython on Waveshare ESP32-S3-ZERO

import espnow
import wifi
import board
import time
import neopixel

channel = 1
rcvd_channel = 0
start_time = 0
dmx_data = bytearray(513)
packet_received = 0

wifi.radio.start_ap(" ", "", channel=channel, max_connections=10)
wifi.radio.stop_ap()
wifi_mac = wifi.radio.mac_address

def mac2Str(wifi_mac): 
    return ':'.join([f"{b:02X}" for b in wifi_mac])

print(f"MAC: {wifi_mac} -> {mac2Str(wifi_mac)}")


print(f"scan starting on channel {channel}...")

e = espnow.ESPNow()

pixel_pin = board.NEOPIXEL
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))

def start_ap(channel):
    print(f"going to channel {channel}")
    wifi.radio.start_ap(b'my_ap', b'password', channel=channel)
    wifi.radio.stop_ap()
    
def start_ap_once_more(channel):
    global packet_received
    if packet_received == 0:
        print(f"got an ESPNow packet that says we're really on channel {channel}")
        packet_received = 1
        start_ap(channel)

def check_for_packet():
    if e:
        return True
    
def update_pixels(dmx_data):
    dmx1 = dmx_data[1]
    dmx2 = dmx_data[2]
    dmx3 = dmx_data[3]
    pixels.fill((dmx2,dmx1,dmx3))

while True:
    
    start_time = time.monotonic()
    while time.monotonic() - start_time < 0.6:
        if check_for_packet():
            try:
                packet = e.read()               
                dmx_data = packet[1]
                channel = dmx_data[0]
                update_pixels(dmx_data)
                start_ap_once_more(channel)
            except:
                pass
            break
    else:
        if packet_received == 0: # No packet received, restart AP and increment channel
            channel = (channel % 11) + 1
            pixels.fill((0,5,0))
            time.sleep(0.05)
            pixels.fill((0,0,0))
            start_ap(channel)

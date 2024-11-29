# Circuitpython on Waveshare ESP32-S3-ZERO
# artnet espnow client/pixel/repeater

import espnow
import wifi
import board
import time
import neopixel
import pwmio

# variables initialization
is_repeater = False # change to True to make this device into a repeater
channel = 1 # scan start channel, adjust to the correct channel to make it connect faster
rcvd_channel = 0
dmx_data = bytearray(513)
packet_received_flag = 0
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
errors = 1 # used to display error count
packet = 0
# old_packet = 0

def start_espnow():
    global e
    e = espnow.ESPNow()
    e.peers.append(peer)
    
def start_ap(channel):
    print(f"going to channel {channel}")
    wifi.radio.start_ap(b'my_ap', b'password', channel=channel)
    wifi.radio.stop_ap()
    
def start_ap_once_more(channel):
    global packet_received_flag
    if packet_received_flag == 0:
        print(f"got an ESPNow packet that says we're on channel {channel}")
        packet_received_flag = 1
        start_ap(channel)
        onboard_pixel.fill((0,5,0)) # onboard LED stays green when correct channel has been reached

def check_for_packet():
    if e:
        return True

def update_pixels(dmx_data):
    dmx1 = dmx_data[1]
    dmx2 = dmx_data[2]
    dmx3 = dmx_data[3]
    dmx4 = dmx_data[4]
    pixels.fill((dmx1,dmx2,dmx3,dmx4))
    pwm.duty_cycle = 65534-(dmx1*255)
    
def read_packet():
    global packet
    global errors
    try:
        packet = e.read()
    except ValueError as error:
        print(f"{error} error {errors}")
        e.deinit()
        start_espnow()
        errors = errors +1
        
print("starting scan")
start_ap(channel)

onboard_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, pixel_order=neopixel.RGB) # onboard neopixel
pixels = neopixel.NeoPixel(board.D1, 1,pixel_order=neopixel.RGBW) # big neopixel connected on digital output 1
pixels.brightness = 1
pixels.fill((0, 0, 0, 0))
pwm = pwmio.PWMOut(board.D7, frequency=1000)
start_espnow()
        
while True:

    if check_for_packet():
        read_packet()
        dmx_data = packet[1]
        channel = dmx_data[0]
        update_pixels(dmx_data)
        if not packet_received_flag: 
            start_ap_once_more(channel)
        if is_repeater:
            e.send(dmx_data,peer)

    else:
        if packet_received_flag == 0: # No packet received, restart AP and increment channel
            channel = (channel % 11) + 1
            onboard_pixel.fill((5,0,0)) # blink red each time we switch channel
            time.sleep(0.05)
            onboard_pixel.fill((0,0,0))
            start_ap(channel)
            time.sleep(0.3)

 

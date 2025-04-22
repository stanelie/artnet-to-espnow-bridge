# Circuitpython on Waveshare ESP32-C3-supermini
# https://circuitpython.org/board/makergo_esp32c3_supermini/
# artnet espnow client/pixel/repeater

import espnow
import wifi
import board
import time
# import neopixel
import pwmio

# CONFIG
dmx_1st_channel = 1
is_repeater = False  # change to True to make this device into a repeater
channel = 1  # radio scan start channel, set to correct channel to connect faster

# variables initialization
rcvd_channel = 0
dmx_data = bytearray(513)
packet_received_flag = 0
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
errors = 1  # used to display error count
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
#        onboard_pixel.fill((0,5,0))  # onboard LED stays green when correct channel has been reached

def check_for_packet():
    if e:
        return True

def update_pixels(dmx_data):
    dmx1 = dmx_data[dmx_1st_channel + 0]
    dmx2 = dmx_data[dmx_1st_channel + 1]
    dmx3 = dmx_data[dmx_1st_channel + 2]
    dmx4 = dmx_data[dmx_1st_channel + 3]
    dmx5 = dmx_data[dmx_1st_channel + 4]
    dmx6 = dmx_data[dmx_1st_channel + 5]
    dmx7 = dmx_data[dmx_1st_channel + 6]
    dmx8 = dmx_data[dmx_1st_channel + 7]
#    pixels.fill((dmx1,dmx3,dmx5,dmx7))
    pwmR.duty_cycle = (dmx1 << 8) | dmx2
    pwmW.duty_cycle = (dmx3 << 8) | dmx4
    pwmG.duty_cycle = (dmx5 << 8) | dmx6
    pwmB.duty_cycle = (dmx7 << 8) | dmx8
#    pwmW.duty_cycle = (dmx1*255)
#    pwmG.duty_cycle = (dmx2*255)
#    pwmB.duty_cycle = (dmx3*255)
#    pwmR.duty_cycle = (dmx4*255)
    
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

# onboard_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, pixel_order=neopixel.RGB) # onboard neopixel
# pixels = neopixel.NeoPixel(board.D1, 1,pixel_order=neopixel.RGBW) # big neopixel connected on digital output 1
# pixels.brightness = 1
# pixels.fill((0, 0, 0, 0))

pwmR = pwmio.PWMOut(board.IO0, frequency=1000)
pwmG = pwmio.PWMOut(board.IO1, frequency=1000)
pwmB = pwmio.PWMOut(board.IO2, frequency=1000)
pwmW = pwmio.PWMOut(board.IO3, frequency=1000)

start_espnow()
        
while True:

    if check_for_packet():
        read_packet()
        dmx_data = packet[1]
        if dmx_data[0] > 0:
            channel = dmx_data[0]
        update_pixels(dmx_data)
        if not packet_received_flag: 
            start_ap_once_more(channel)
        if is_repeater:
            e.send(dmx_data,peer)

    else:
        if packet_received_flag == 0: # No packet received, restart AP and increment channel
            channel = (channel % 11) + 1
#            onboard_pixel.fill((5,0,0)) # blink red each time we switch channel
            time.sleep(0.05)
#            onboard_pixel.fill((0,0,0))
            start_ap(channel)
            time.sleep(0.3)

 


# Circuitpython on Waveshare ESP32-S3-ZERO
# artnet espnow client/pixel

import espnow
import wifi
import board
import time
import neopixel
import microcontroller

channel = 1
rcvd_channel = 0
dmx_data = bytearray(513)
packet_received_flag = 0

wifi.radio.start_ap(" ", "", channel=channel, max_connections=10)
wifi.radio.stop_ap()
wifi_mac = wifi.radio.mac_address

def mac2Str(wifi_mac): 
    return ':'.join([f"{b:02X}" for b in wifi_mac])

print(f"MAC: {wifi_mac} -> {mac2Str(wifi_mac)}")

print(f"scan starting on channel {channel}...")

peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')

def start_espnow():
    global e
    e = espnow.ESPNow()
    e.peers.append(peer)
    
start_espnow()

pixel_pin = board.NEOPIXEL
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))

def start_ap(channel):
    print(f"going to channel {channel}")
    wifi.radio.start_ap(b'my_ap', b'password', channel=channel)
    wifi.radio.stop_ap()
    
def start_ap_once_more(channel):
    global packet_received_flag
    if packet_received_flag == 0:
        print(f"got an ESPNow packet that says we're really on channel {channel}")
        packet_received_flag = 1
        start_ap(channel)

def check_for_packet():
    if e:
        return True
    
def update_pixels(dmx_data):
    dmx1 = dmx_data[1]
    dmx2 = dmx_data[2]
    dmx3 = dmx_data[3]
    pixels.fill((dmx2,dmx1,dmx3))
packet = 0
def read_packet():
    global packet
    try:
        packet = e.read()
    except ValueError as error:
        print(f"{error}")
        time.sleep(0.1)
#        microcontroller.reset()
        e.deinit()
        start_espnow()
        
old_packet = 0

while True:
    if check_for_packet():
        read_packet()
        if packet[1] != old_packet:
            dmx_data = packet[1]
            channel = dmx_data[0]
            update_pixels(dmx_data)
            start_ap_once_more(channel)
#            e.send(dmx_data,peer)
            old_packet = packet[1]
#            print(f"{packet[0]}")

    else:
        if packet_received_flag == 0: # No packet received, restart AP and increment channel
            channel = (channel % 11) + 1
            pixels.fill((0,5,0))
            time.sleep(0.05)
            pixels.fill((0,0,0))
            start_ap(channel)
            time.sleep(0.3)



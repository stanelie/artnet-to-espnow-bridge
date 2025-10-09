# Circuitpython on Waveshare ESP32-S3-ZERO or ESP32-C3-mini
# artnet/DMX espnow client/pixel/repeater

import espnow
import wifi
import board
import time
import neopixel
import pwmio

# CONFIG
dmx_start_addr = 1
is_repeater = False  # change to True to make this device into a repeater
channel = 6  # radio scan start channel, set to correct channel to connect faster

# variables initialization
rcvd_channel = 0
dmx_data = bytearray(513)
packet_received_flag = 0
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
errors = 1  # used to display error count
packet = None # Using None to indicate no packet read yet
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
        onboard_pixel.fill((0,5,0))  # onboard LED stays green when correct channel has been reached

def check_for_packet():
    if e:
        return True
    return False

def update_pixels(dmx_data):
    # print("updating_outputs")
    onboard_pixel.fill((dmx_data[dmx_start_addr + 0], dmx_data[dmx_start_addr + 2], dmx_data[dmx_start_addr + 4], dmx_data[dmx_start_addr + 6]))
    pwmR.duty_cycle = (dmx_data[dmx_start_addr + 0] << 8) | dmx_data[dmx_start_addr + 1]
    pwmW.duty_cycle = (dmx_data[dmx_start_addr + 2] << 8) | dmx_data[dmx_start_addr + 3]
    pwmG.duty_cycle = (dmx_data[dmx_start_addr + 4] << 8) | dmx_data[dmx_start_addr + 5]
    pwmB.duty_cycle = (dmx_data[dmx_start_addr + 6] << 8) | dmx_data[dmx_start_addr + 7]
    
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
        packet = None # Ensure packet is None on error
        
print("starting scan")
start_ap(channel)

onboard_pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, pixel_order=neopixel.RGB) # onboard neopixel
# pixels = neopixel.NeoPixel(board.D1, 1,pixel_order=neopixel.RGBW) # big neopixel connected on digital output 1
# pixels.brightness = 1
# pixels.fill((0, 0, 0, 0))

pwmR = pwmio.PWMOut(board.D3, frequency=2500)
pwmG = pwmio.PWMOut(board.D4, frequency=2500)
pwmB = pwmio.PWMOut(board.D5, frequency=2500)
pwmW = pwmio.PWMOut(board.D6, frequency=2500)

start_espnow()
        
while True:

    if check_for_packet():
        read_packet() # This function updates the global 'packet' variable

        # Check if a packet was successfully read and is not None
        if packet:
            payload = packet[1]

            # Ensure the payload has at least the 2-byte header
            if len(payload) >= 2:
                # --- MODIFIED LOGIC START ---
                
                # Extract header information
                rcvd_channel = payload[0]
                packet_num = payload[1]

                # Extract the DMX data part of the payload (from the 3rd byte onwards)
                partial_dmx = payload[2:]
                partial_dmx_len = len(partial_dmx)

                # Update the correct slice of the main dmx_data buffer
                if packet_num == 1:
                    # Packet for DMX addresses 1-180
                    dmx_data[1 : 1 + partial_dmx_len] = partial_dmx
                elif packet_num == 2:
                    # Packet for DMX addresses 181-360
                    dmx_data[181 : 181 + partial_dmx_len] = partial_dmx
                
                # Always call update_pixels after receiving and processing a packet
                update_pixels(dmx_data)

                # --- MODIFIED LOGIC END ---

                # Update the channel for the AP setup logic
                if rcvd_channel > 0:
                    channel = rcvd_channel

                # Run the one-time AP setup if it hasn't run yet
                if not packet_received_flag: 
                    start_ap_once_more(channel)
                
                # If this device is a repeater, re-send the original received packet
                if is_repeater:
                    e.send(payload, peer)

    else:
        # This part handles channel scanning if no packets are ever received
        if packet_received_flag == 0: 
            channel = (channel % 11) + 1
            onboard_pixel.fill((5,0,0)) # blink red each time we switch channel
            time.sleep(0.05)
            onboard_pixel.fill((0,0,0))
            start_ap(channel)
            time.sleep(0.3)


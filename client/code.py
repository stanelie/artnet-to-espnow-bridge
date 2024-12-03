# Circuitpython on Waveshare ESP32-S3-ZERO
# artnet to espnow bridge

import socketpool
import wifi
import time
import board
import os
import neopixel
import espnow
from config import *
import digitalio
import busio
import adafruit_rfm9x
import ipaddress
import supervisor

#
# the wifi config is in a config.py file at the same level as this file
#

USE_STATIC_IP = True
HOSTNAME = "lonestar-bridge"
artnet_universe = UNIVERSE

wifi_mac = wifi.radio.mac_address
ip_address_str = 0
wifi_channel = 0

# setup IP stuff if we do not use DHCP
ip_byte = bytes([2,(0x2B + 0xFA + wifi_mac[3]) & 0xFF,wifi_mac[4],wifi_mac[5]]) # derive IP address from MAC address and OEM code
ipv4 = ipaddress.IPv4Address(ip_byte)
netmask = ipaddress.IPv4Address("255.0.0.0")
gateway = ipaddress.IPv4Address("2.0.0.1")

def connect_to_wifi():
    try:
        print(f"connecting wifi to \"{SSID}\"...")
        wifi.radio.hostname = HOSTNAME
        if USE_STATIC_IP:
            wifi.radio.set_ipv4_address(ipv4 = ipv4, netmask = netmask, gateway = gateway) # use static IP address
        wifi.radio.connect(SSID,PASSWORD, timeout=5)
        global ip_address_str
        ip_address_str = str(wifi.radio.ipv4_address)
        global wifi_channel
        wifi_channel = wifi.radio.ap_info.channel
    except ConnectionError as e:
        print(f"{e} . Retrying...")
        wifi.radio.stop_station()
        time.sleep(1)
        connect_to_wifi()
        
def create_wifi_AP():
    print(f"setting up wifi access point \"{SSID}\"...")
    CHANNEL = 1
    wifi.radio.hostname = HOSTNAME
    wifi.radio.set_ipv4_address_ap(ipv4 = ipv4, netmask = netmask, gateway = gateway) # use static IP address
    wifi.radio.start_ap(SSID, PASSWORD, channel=CHANNEL, max_connections=4)
    time.sleep(0.01) # bug : needed so IP is available in ip_address_str
    global ip_address_str
    ip_address_str = str(wifi.radio.ipv4_address_ap)
    global wifi_channel
    wifi_channel = CHANNEL

connect_to_wifi() # connect to access point as wifi client
# create_wifi_AP() # creates wifi access point

hostname_bytes = wifi.radio.hostname.encode('utf-8')

print(f"UP! my IP addr: {ip_address_str}, channel {wifi_channel}" )

# setup LoRa radio
RADIO_FREQ_MHZ = 433.0
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D7)
spi = busio.SPI(board.D2, MOSI=board.D3, MISO=board.D4)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
rfm9x.tx_power = 23 # 23 is strongest
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 250000
rfm9x.coding_rate = 5

# massage ipaddress
octets = ip_address_str.split('.')
ip_address_bytes = bytearray(4)
for i in range(4):
    ip_address_bytes[i] = int(octets[i])
    
pixel_pin = board.NEOPIXEL
# ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))

pool = socketpool.SocketPool(wifi.radio)

# udp_host = str(wifi.radio.ipv4_address) # my LAN IP as a string
udp_buffer = bytearray(572)  # stores our incoming packet

sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # UDP socket
sock.bind(('0.0.0.0', 6454))# say we want to listen on this host,port
sock.settimeout(0)

last_sent_time = time.monotonic()

reply_array = [
                0x41, 0x72, 0x74, 0x2d, 0x4e, 0x65, 0x74, 0x00, # "Art-Net\0" header
                0x00, 0x21,                                     # opcode
                0x02, 0xe7, 0x14, 0x24,                         # our IP address
                0x36, 0x19,                                     # port 6454
                0x00, 0x01,                                     # version info of this node
                0x00,                                           # NetSwitch
                0x00,                                           # SubSwitch (universe?)
                0x2B, 0xFA,                                     # OEM code (Ex Machina is 2BFA)
                0x00,                                           # UBEA version #
                0xF0,                                           # status
                0x00, 0x00,                                     # ESTA manufacturer code
                0x73, 0x6c, 0x65, 0x73, 0x61, 0x2d, 0x69, 0x70, # Short Name 18 bytes
                0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00,
                0x73, 0x6c, 0x65, 0x73,               
                0x61, 0x2d, 0x69, 0x70, 0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x80, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x50, 0xc2, 0x37, 0x14, 0x24,             # our mac address
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                ]
# IP address
reply_array[10] = ip_address_bytes[0]
reply_array[11] = ip_address_bytes[1]
reply_array[12] = ip_address_bytes[2]
reply_array[13] = ip_address_bytes[3]

# mac address
reply_array[201] = wifi_mac[0]
reply_array[202] = wifi_mac[1]
reply_array[203] = wifi_mac[2]
reply_array[204] = wifi_mac[3]
reply_array[205] = wifi_mac[4]
reply_array[206] = wifi_mac[5]

# Short name
num_bytes_to_replace = len(hostname_bytes)
end_index = min(26 + num_bytes_to_replace, len(reply_array))
modified_portion = bytearray(reply_array[:26]) + hostname_bytes + bytearray(reply_array[end_index:])
reply_array = modified_portion

# Long name
num_bytes_to_replace = len(hostname_bytes)
end_index = min(44 + num_bytes_to_replace, len(reply_array))
modified_portion = bytearray(reply_array[:44]) + hostname_bytes + bytearray(reply_array[end_index:])
reply_array = modified_portion

# Universe
reply_array[190] = artnet_universe - 1

reply = bytes(reply_array)

e = espnow.ESPNow()
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
e.peers.append(peer)

dmx_data = bytearray(513)

while True:
#    if wifi.radio.connected:
    sock.settimeout(0.2)
    try:
        size, addr = sock.recvfrom_into(udp_buffer)
        msg = bytes(udp_buffer)
    
        if msg[:8] == b'Art-Net\0': # Check if the received data is an Art-Net packet

            if msg[9:11] == b'\x20\x00': # is artpoll
                print(f"artpoll packet from {addr[0]}")
                sock.sendto(reply, (addr[0],6454) )
                print(f"Artpoll reply sent to {addr[0]}")
            
            if msg[9:11] == b'\x50\x00': # is artnet DMX channel data
                if msg[14] == (artnet_universe - 1):
                    dmx_data[0] = wifi_channel # send wifi channel as first byte of the transmission
                    dmx_data[1:] = msg[(17+STARTDMX):531] # send the DMX channels
                    pixels.fill((dmx_data[2], dmx_data[1], dmx_data[3]))
                    e.send(dmx_data[0:50], peer) # send 250 bytes max (espnow limitation)
                    rfm9x.send(dmx_data[0:50])
    except:
        pass
            
    if time.monotonic() - last_sent_time >= 0.3:
        e.send(dmx_data[0:50], peer) # resend last dmx values as beacon
        rfm9x.send(dmx_data[0:50])
        last_sent_time = time.monotonic()

#    else:
#        connect_to_wifi()






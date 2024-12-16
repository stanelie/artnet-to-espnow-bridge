# Circuitpython on Waveshare ESP32-S3-ETH
# artnet to espnow bridge
#
# Config is in the config.py file
#

import wifi
import time
import board
import os
import neopixel
import espnow
from config import *
import digitalio
import busio
import ipaddress

wifi.radio.hostname = HOSTNAME
hostname_bytes = HOSTNAME.encode('utf-8')
wifi_mac = wifi.radio.mac_address
ip_address_str = 0
wifi_channel = 0
last_sent_time = time.monotonic()
dmx_data = bytearray(513)
netmask = "255.0.0.0"
gateway: str = "2.0.0.1"
dns: str = "2.0.0.1"

if NETWORK_MODE == "STA" or NETWORK_MODE == "AP":
    import socketpool
    pool = socketpool.SocketPool(wifi.radio)
    ip_byte = bytes([2,(0x2B + 0xFA + wifi_mac[3]) & 0xFF,wifi_mac[4],wifi_mac[5]]) # derive IP address from MAC address and OEM code
    ipv4 = ipaddress.IPv4Address(ip_byte)

if NETWORK_MODE == "ETH":
    import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
    from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
    # For ESP32-S3-ETH
    cs = digitalio.DigitalInOut(board.GPIO14)
    rst = digitalio.DigitalInOut(board.GPIO9)
    spi = busio.SPI(board.GPIO13, MOSI=board.GPIO11, MISO=board.GPIO12)
    print(f"connecting to ethernet...")
    eth = WIZNET5K(spi, cs, reset=rst, is_dhcp=USE_DHCP, debug=False)
    pool = socketpool.SocketPool(eth)
    if not USE_DHCP:
        ip_byte = bytes([2,(0x2B + 0xFA + eth.mac_address[3]) & 0xFF,eth.mac_address[4],eth.mac_address[5]])
        ipv4 = ipaddress.IPv4Address(ip_byte)
        ipv4 = str(ipv4)
        eth.ifconfig = tuple(pool.inet_aton(num) for num in (ipv4, netmask, gateway, dns))
    print("ethernet up!")

    
pixel_pin = board.NEOPIXEL
# ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))

def connect_to_wifi():
    while not wifi.radio.connected:
        try:
            print(f"connecting wifi to \"{SSID}\"...")
            if not USE_DHCP:
                wifi.radio.set_ipv4_address(ipv4 = ipv4, netmask = netmask, gateway = gateway) # use static IP address
            wifi.radio.connect(SSID,PASSWORD, timeout=5)
        except ConnectionError as e:
            print(f"{e} . Retrying...")
    global ip_address_str
    ip_address_str = str(wifi.radio.ipv4_address)
    global wifi_channel
    wifi_channel = wifi.radio.ap_info.channel

def create_wifi_AP():
    print(f"setting up wifi access point \"{SSID}\"...")
    wifi.radio.set_ipv4_address_ap(ipv4 = ipv4, netmask = netmask, gateway = gateway)
    wifi.radio.start_ap(SSID, PASSWORD, channel=CHANNEL, max_connections=4)
    time.sleep(0.01) # bug : needed so IP is available in ip_address_str
    global ip_address_str
    ip_address_str = str(wifi.radio.ipv4_address_ap)
    global wifi_channel
    wifi_channel = CHANNEL
    
def connect_eth():
    print("My IP address is:", eth.pretty_ip(eth.ip_address))
    wifi.radio.start_ap(SSID, PASSWORD, channel=CHANNEL, max_connections=4)
    wifi.radio.stop_ap()
    global ip_address_str
    ip_address_str = str(eth.pretty_ip(eth.ip_address))
    time.sleep(1)

udp_buffer = bytearray(572)  # stores our incoming packet

reply_array = (
                b'\x41' b'\x72' b'\x74' b'\x2d' b'\x4e' b'\x65' b'\x74' b'\x00' # "Art-Net\0" header
                b'\x00' b'\x21'                                                 # opcode
                b'\x02' b'\x00' b'\x00' b'\x01'                                 # our IP address
                b'\x36' b'\x19'                                                 # port 6454
                b'\x00' b'\x01'                                                 # version info of this node
                b'\x00'                                                         # NetSwitch
                b'\x00'                                                         # SubSwitch (universe?)
                b'\x2B' b'\xFA'                                                 # OEM code (Ex Machina is 2BFA)
                b'\x00'                                                         # UBEA version #
                b'\xF0'                                                         # status
                b'\x00' b'\x00'                                                 # ESTA manufacturer code
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' # Short Name 18 bytes
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00'               
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x01' b'\x80' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x80' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x50' b'\xc2' b'\x37' b'\x14' b'\x24'                 # our mac address
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'
                )

def format_reply_array():
    octets = ip_address_str.split('.')   
    ip_address_bytes = bytearray(4)
    for i in range(4):
        ip_address_bytes[i] = int(octets[i])
    global reply_array
    reply_array[10] = ip_address_bytes[0]
    reply_array[11] = ip_address_bytes[1]
    reply_array[12] = ip_address_bytes[2]
    reply_array[13] = ip_address_bytes[3]
    
    if NETWORK_MODE == "ETH":
#        print(f"ethernet mac : {eth.mac_address}")
        reply_array[201] = eth.mac_address[0]
        reply_array[202] = eth.mac_address[1]
        reply_array[203] = eth.mac_address[2]
        reply_array[204] = eth.mac_address[3]
        reply_array[205] = eth.mac_address[4]
        reply_array[206] = eth.mac_address[5]
    if NETWORK_MODE == "STA" or NETWORK_MODE == "AP":
#        print(f"ethernet mac : {wifi_mac}")
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
reply_array[190] = UNIVERSE - 1

def start_network():
    if NETWORK_MODE == "STA":
        connect_to_wifi()
    if NETWORK_MODE == "AP":
        create_wifi_ap()
    if NETWORK_MODE == "ETH":
        connect_eth()
        
start_network()

e = espnow.ESPNow()
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
e.peers.append(peer)



    
sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # UDP socket
sock.bind(("", 6454))# say we want to listen on this host,port
sock.settimeout(0)    
MAXBUF = 572
print("listening for Artnet...")

while True:
    
    if wifi.radio.connected or eth.link_status:
        
        try:
            size, addr = sock.recvfrom_into(udp_buffer, MAXBUF)
            msg = bytes(udp_buffer)
        
            if msg[:8] == b'Art-Net\0': # Check if the received data is an Art-Net packet

                if msg[9:11] == b'\x20\x00': # is artpoll
                    print(f"artpoll packet from {addr[0]}")
                    format_reply_array()
                    reply = bytes(reply_array)
                    sock.sendto(reply, (addr[0],6454) )
                    print(f"Artpoll reply sent to {addr[0]}")
                    udp_buffer[1:] = b'\x00' * MAXBUF
                
                if msg[9:11] == b'\x50\x00': # is artnet DMX channel data
#                    print("dmx!")
                    if msg[14] == (UNIVERSE - 1):
                        if NETWORK_MODE == "ETH" or NETWORK_MODE == "AP":
                            dmx_data[0] = CHANNEL
                        if NETWORK_MODE == "STA":
                            dmx_data[0] = wifi_channel # send wifi channel as first byte of the transmission
                        dmx_data[1:] = msg[(17+STARTDMX):531] # send the DMX channels
                        pixels.fill((dmx_data[2], dmx_data[1], dmx_data[3]))
                        e.send(dmx_data[0:50], peer) # send 250 bytes max (espnow limitation)

        except:
            pass
                
        if time.monotonic() - last_sent_time >= 0.3:
            e.send(dmx_data[0:50], peer) # resend last dmx values as beacon
            last_sent_time = time.monotonic()
            print("repeat")
    else:
        time.sleep(1)
        start_network()

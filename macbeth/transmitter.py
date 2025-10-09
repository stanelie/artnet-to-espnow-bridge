# artnet transmitter over ESP-Now, for ESP32-S3-ETH
# needs a config.py file containing the following :
#
# SSID = "artnet"             # nom du réseau wifi
# PASSWORD = "aaaaaaaaaa"     # clé réseau wifi
# CHANNEL = 6                 # wifi AP channel and ESPnow channel when in ETH mode
# NETWORK_MODE = "ETH"        # "ETH" for ethernet, "STA" for station, "AP" for access point
# USE_DHCP = False            # ignored if NETWORK_MODE = "AP"
# HOSTNAME = "lonestar-bridge"
#
# STARTDMX = 1                # first DMX channel
# UNIVERSE = 0                # listen universe


import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socketpool
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
import wifi
import espnow
import digitalio
import busio
import board
import time
from config import *
import neopixel
import ipaddress

cs = digitalio.DigitalInOut(board.IO14)
rst = digitalio.DigitalInOut(board.IO9)
spi = busio.SPI(board.IO13, MOSI=board.IO11, MISO=board.IO12)

socket_started = False
ip_address_str = 0
hostname_bytes = HOSTNAME.encode('utf-8')
last_sent_time = time.monotonic()
MAXBUF = 572
udp_buffer = bytearray(572)  # stores our incoming packet
dmx_data = bytearray(513)
netmask = "255.0.0.0"
gateway: str = "2.0.0.1"
dns: str = "2.0.0.1"

# setup IO0 pin as witness for sending espnow
PIN = board.IO0
io0 = digitalio.DigitalInOut(PIN)
io0.direction = digitalio.Direction.OUTPUT

pixel_pin = board.NEOPIXEL
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, pixel_order=ORDER)
pixels.fill((0, 0, 0))

reply_array = bytearray(
                b'\x41' b'\x72' b'\x74' b'\x2d' b'\x4e' b'\x65' b'\x74' b'\x00'  # "Art-Net\0" header
                b'\x00' b'\x21'                                                  # opcode
                b'\x02' b'\x00' b'\x00' b'\x01'                                  # our IP address
                b'\x36' b'\x19'                                                  # port 6454
                b'\x00' b'\x01'                                                  # version info of this node
                b'\x00'                                                          # NetSwitch
                b'\x00'                                                          # SubSwitch (universe?)
                b'\x2B' b'\xFA'                                                  # OEM code (Ex Machina is 2BFA)
                b'\x00'                                                          # UBEA version #
                b'\xF0'                                                          # status
                b'\x00' b'\x00'                                                  # ESTA manufacturer code
                b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00' b'\x00'  # Short Name 18 bytes
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


def start_socket_eth():
    pool = socketpool.SocketPool(eth)
    global sock
    sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    sock.bind(("", 6454))
    sock.settimeout(0)  
    socket_started = True
    wifi.radio.start_ap(SSID, PASSWORD, channel=CHANNEL, max_connections=4)
    wifi.radio.stop_ap()
    if not USE_DHCP:
        ip_byte = bytes([2,(0x2B + 0xFA + eth.mac_address[3]) & 0xFF,eth.mac_address[4],eth.mac_address[5]])
        ipv4 = ipaddress.IPv4Address(ip_byte)
        ipv4 = str(ipv4)
        eth.ifconfig = tuple(pool.inet_aton(num) for num in (ipv4, netmask, gateway, dns))
        
    global ip_address_str
    ip_address_str = str(eth.pretty_ip(eth.ip_address))
    print("My IP address is:", eth.pretty_ip(eth.ip_address))
    format_reply_array()
    
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
    #  print(f"ethernet mac : {eth.mac_address}")
        reply_array[201] = eth.mac_address[0]
        reply_array[202] = eth.mac_address[1]
        reply_array[203] = eth.mac_address[2]
        reply_array[204] = eth.mac_address[3]
        reply_array[205] = eth.mac_address[4]
        reply_array[206] = eth.mac_address[5]
    if NETWORK_MODE == "STA" or NETWORK_MODE == "AP":
    #  print(f"ethernet mac : {wifi_mac}")
        reply_array[201] = wifi_mac[0]
        reply_array[202] = wifi_mac[1]
        reply_array[203] = wifi_mac[2]
        reply_array[204] = wifi_mac[3]
        reply_array[205] = wifi_mac[4]
        reply_array[206] = wifi_mac[5]

    #  Short name
    num_bytes_to_replace = len(hostname_bytes)
    end_index = min(26 + num_bytes_to_replace, len(reply_array))
    modified_portion = bytearray(reply_array[:26]) + hostname_bytes + bytearray(reply_array[end_index:])
    reply_array = modified_portion

    #  Long name
    num_bytes_to_replace = len(hostname_bytes)
    end_index = min(44 + num_bytes_to_replace, len(reply_array))
    modified_portion = bytearray(reply_array[:44]) + hostname_bytes + bytearray(reply_array[end_index:])
    reply_array = modified_portion

    # Universe
    reply_array[190] = UNIVERSE
    
def process_packet():
    size, addr = sock.recvfrom_into(udp_buffer, MAXBUF)
    msg = bytes(udp_buffer)
    if msg[:8] == b'Art-Net\0':  # Check if the received data is an Art-Net packet
        if msg[9:11] == b'\x20\x00':  # is artpoll
            print(f"artpoll packet from {addr[0]}")
            format_reply_array()
            reply = bytes(reply_array)
            sock.sendto(reply, (addr[0],6454) )
            print(f"Artpoll reply sent to {addr[0]}")
            udp_buffer[1:] = b'\x00' * MAXBUF
        if msg[9:11] == b'\x50\x00':  # is artnet DMX channel data
            # print("dmx!")
            # print(f"received universe {msg[14]}")
            if msg[14] == (UNIVERSE):
                # --- Constants ---
                DMX_CHANNELS_PER_PACKET = 180
                PACKET_HEADER_SIZE = 2  # 1 byte for wifi_channel, 1 byte for packet number
                PACKET_SIZE = PACKET_HEADER_SIZE + DMX_CHANNELS_PER_PACKET
                current_channel = 0
                
                # --- Create Packet Buffers ---
                # We will create two separate bytearray objects for our packets.
                packet1 = bytearray(PACKET_SIZE)
                packet2 = bytearray(PACKET_SIZE)

                if NETWORK_MODE == "STA":
                    # For Station mode, use the dynamically obtained Wi-Fi channel
                    current_channel = wifi_channel
                else:
                    # For Ethernet or Access Point mode, use the pre-defined constant CHANNEL
                    current_channel = CHANNEL
                
                packet1[0]  = current_channel  # Byte 0: WiFi channel
                packet2[0]  = current_channel  # Byte 0: WiFi channel

                
                # Assuming STARTDMX is defined elsewhere in your code
                dmx_start_index = 17 + STARTDMX
                
                # --- Prepare and Send Packet 1 (DMX Channels 1-180) ---
                
                # Set the header for the first packet
                packet1[1] = 1             # Byte 1: Packet number
                
                # Slice the DMX data for the first packet from the main message buffer
                dmx_data_for_packet1 = msg[dmx_start_index : dmx_start_index + DMX_CHANNELS_PER_PACKET]
                packet1[2:] = dmx_data_for_packet1
                
                
                # --- Prepare and Send Packet 2 (DMX Channels 181-360) ---
                
                # Set the header for the second packet
                packet2[1] = 2             # Byte 1: Packet number
                
                # Calculate the starting index for the second chunk of DMX data
                packet2_dmx_start = dmx_start_index + DMX_CHANNELS_PER_PACKET
                packet2_dmx_end = packet2_dmx_start + DMX_CHANNELS_PER_PACKET
                
                # Slice the DMX data for the second packet
                dmx_data_for_packet2 = msg[packet2_dmx_start:packet2_dmx_end]
                packet2[2:] = dmx_data_for_packet2
                
                
                # --- Update Local Hardware and Transmit ---
                
                # Update the NeoPixels using the data from the first packet's slice.
                # dmx_data_for_packet1[0] is DMX channel 1 (Red)
                # dmx_data_for_packet1[2] is DMX channel 3 (Green)
                # dmx_data_for_packet1[4] is DMX channel 5 (Blue)
                pixels.fill((dmx_data_for_packet1[0], dmx_data_for_packet1[2], dmx_data_for_packet1[4]))
                
                # Toggle the indicator pin and send both packets in quick succession
                io0.value = True
                e.send(packet1, peer)
                io0.value = False
                time.sleep(0.005)  # small 5 ms pause between packets
                io0.value = True
                e.send(packet2, peer)
                io0.value = False
                
    global last_sent_time            
    if time.monotonic() - last_sent_time >= 0.3:
        e.send(dmx_data[0:50], peer)  # resend last dmx values as beacon
        last_sent_time = time.monotonic()
        
e = espnow.ESPNow()
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
e.peers.append(peer)

while True:
    
        if NETWORK_MODE == "ETH":
            try:
                print(f"connecting to ethernet...")
                eth = WIZNET5K(spi, cs, reset=rst, is_dhcp=USE_DHCP, debug=False)
                
                if eth.link_status:
                    print("link up!")
                    if not socket_started:
                        start_socket_eth()

                while eth.link_status:
                    #  print("processing packet")
                    process_packet()
                else:
                    print("link down...")
            
            except ConnectionError as wiznet5k_error:
                print(wiznet5k_error)






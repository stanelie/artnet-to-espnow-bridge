# Circuitpython on Waveshare ESP32-S3-ZERO
# artnet to espnow bridge

import socketpool
import wifi
import time
import board
import neopixel
import espnow
# import microcontroller

# microcontroller.cpu.frequency = 80000000
# print(f"cpu freq : {microcontroller.cpu.frequency}")

SSID = "sticks"
PASSWORD = "patateaufour"

# import ipaddress
# 
# ipv4 = ipaddress.IPv4Address("2.0.0.2")
# netmask = ipaddress.IPv4Address("255.0.0.0")
# gateway = ipaddress.IPv4Address("2.0.0.1")
# 
# wifi.radio.set_ipv4_address_ap(ipv4=ipv4, netmask=netmask, gateway=gateway)
# wifi.radio.start_ap("artnet_bridge", "aaaaaaaaaa", channel=1, max_connections=4)
# # wifi.radio.stop_ap()

def scan_for_wifi():
    networks = []
    for network in wifi.radio.start_scanning_networks():
        networks.append(network)
    wifi.radio.stop_scanning_networks()
    networks = sorted(networks, key=lambda net: net.rssi, reverse=False)
    for network in networks:
#        print("ssid:",network.ssid, "rssi:",network.rssi)
        if network.ssid == SSID:
            print(f"network \"{SSID}\" is present!")
            return True
        
def connect_to_wifi():
    print(f"connecting wifi to \"{SSID}\"...")
    wifi.radio.connect(SSID,PASSWORD)


if scan_for_wifi():
    connect_to_wifi()
else:
    print(f"wifi \"{SSID}\" absent, retrying in 2 seconds...")
    scan_for_wifi()


wifi.radio.hostname = "lonestar-bridge"
hostname_bytes = wifi.radio.hostname.encode('utf-8')
wifi_mac = wifi.radio.mac_address
ip_address_str = wifi.radio.ipv4_address

for network in wifi.radio.start_scanning_networks():
    if network.ssid == SSID:
        channel = network.channel
wifi.radio.stop_scanning_networks()

print(f"connected, my IP addr: {ip_address_str}, channel {channel}" )

# massage ipaddress
ip_address_str = str(wifi.radio.ipv4_address)
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
                0x00,                                           # SubSwitch
                0x2B, 0xFA,                                     # OEM code (Ex Machina is 2BFA)
                0x00, 0xe0, 0x00, 0x00, 0x73, 0x6c, 0x65, 0x73, 0x61, 0x2d,
				0x69, 0x70, 0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x73, 0x6c, 0x65, 0x73,               
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

reply = bytes(reply_array)

e = espnow.ESPNow()
peer = espnow.Peer(b'\xff\xff\xff\xff\xff\xff')
# peer = espnow.Peer(b'$\xecJ&\x8d\xb0')
# peer = espnow.Peer(mac=b'$\xecJ&\x8d\xb0')
e.peers.append(peer)

dmx_data = bytearray(513)

while True:
    
    sock.settimeout(0.2)
    try:
        size, addr = sock.recvfrom_into(udp_buffer)
        msg = bytes(udp_buffer)
    
        if msg[:8] == b'Art-Net\0': # Check if the received data is an Art-Net packet

            if msg[9:11] == b'\x20\x00': # is artpoll
                print(f"artpoll packet from {addr[0]}")
                sock.sendto(reply, (addr[0],6454) )
                print(f"Artpoll reply sent to {addr[0]}")
            
            if msg[9:11] == b'\x50\x00': # is artnet channel data
#                print ("DMX!")
                dmx_data[0] = channel # send wifi channel as first byte of the transmission
                dmx_data[1:] = msg[18:531] # send the DMX channels
                pixels.fill((dmx_data[2], dmx_data[1], dmx_data[3]))
#                print(dmx_data[2])
                e.send(dmx_data[0:10], peer) # send 250 bytes max (espnow limitation)
    except:
        pass
            
    if time.monotonic() - last_sent_time >= 0.5:
        e.send(dmx_data[0:10], peer) # resend last dmx values as beacon
        last_sent_time = time.monotonic()
        print("resend")
#        print(f"cpu temp: {microcontroller.cpu.temperature}")



import digitalio
import board
import busio
import adafruit_rfm9x
import neopixel

RADIO_FREQ_MHZ = 433.0
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D7)
spi = busio.SPI(board.D2, MOSI=board.D3, MISO=board.D4)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

pixel_pin = board.NEOPIXEL
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 0, 0))
rfm9x.tx_power = 23
rfm9x.spreading_factor = 7
rfm9x.signal_bandwidth = 250000
rfm9x.coding_rate = 5

while True:
    
    packet = rfm9x.receive(timeout=10)
    if packet is None:
        pixels.fill((0, 0, 0))
#        print("Received nothing! Listening again...")
    else:
        pixels.fill((packet[2], packet[1], packet[3]))
#        print("Received: {0}".format(packet))
#        pixels.fill((0,0,0))

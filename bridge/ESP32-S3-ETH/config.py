# configuration du bridge artnet-ESPNow

SSID = "artnet"             # nom du réseau wifi
PASSWORD = "aaaaaaaaaa"     # clé réseau wifi
CHANNEL = 6                 # wifi AP channel and ESPnow channel when in ETH mode
NETWORK_MODE = "ETH"        # "ETH" for ethernet, "STA" for station, "AP" for access point
USE_DHCP = False            # ignored if NETWORK_MODE = "AP"
HOSTNAME = "lonestar-bridge"

STARTDMX = 1                # first DMX channel
UNIVERSE = 1                # listen universe

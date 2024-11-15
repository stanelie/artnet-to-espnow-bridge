import time
import wifi

# Replace with your SSID and password
SSID = "sticks"
PASSWORD = "patateaufour"

def connect_to_wifi():
    try:
        print(f"Connecting to '{SSID}'...")
        wifi.radio.connect(SSID, PASSWORD)
        time.sleep(0.5)
    except ConnectionError as e:
        print(f"{e} . Retrying...")
        time.sleep(0.5)


while True:
    if wifi.radio.connected:
        print("do shit")
        time.sleep(1)
    else:
        connect_to_wifi()

from ota import OTAUpdater
from constants import ssid, password
import network
from time import sleep
import logger

def connect_wifi(ssid, password):
    """ Connect to Wi-Fi."""

    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(ssid, password)
    while not sta_if.isconnected():
        print('.', end="")
        sleep(0.25)
    print(f'Connected to WiFi, IP is: {sta_if.ifconfig()[0]}')

connect_wifi(ssid, password)

repo_url = "https://github.com/BigyuccaGit/mqtt/"#"https://github.com/kevinmcaleer/ota_test/main/"

logger.init()
ota_updater = OTAUpdater(repo_url)

#ota_updater.download_and_install_update_if_available()

ota_updater.loop_over_updates()
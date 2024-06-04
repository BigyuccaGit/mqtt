from ota import OTAUpdater
from constants import ssid, password

firmware_url = "https://github.com/BigyuccaGit/mqtt/"#"https://github.com/kevinmcaleer/ota_test/main/"

ota_updater = OTAUpdater(ssid, password, firmware_url, "dummy.py")

ota_updater.download_and_install_update_if_available()
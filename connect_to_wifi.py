from machine import Pin
import network
import constants
import logger
import time

# Connect to WiFi
def connect_to_wifi(wifi_retry, minutes):
    
    wlan_status = {
            network.STAT_IDLE:"IDLE",
            network.STAT_CONNECTING:"CONNECTING",
            network.STAT_WRONG_PASSWORD: "WRONG_PASSWORD",
            network.STAT_NO_AP_FOUND: "NO_AP_FOUND",
            network.STAT_CONNECT_FAIL: "CONNECT_FAIL",
            network.STAT_GOT_IP: "CONNECTION SUCCESSFUL"
        }
    
    """ Connect to wi fi """ 
    connected = False
    while not connected:
        pin=Pin("LED", Pin.OUT)
        pin.high()
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)        
        wlan.connect(constants.ssid, constants.password)
        
        # Try several times to connect
        count = 10
        while count > 0:
            connected = wlan.isconnected()
            wstatus = wlan.status()
            if not connected:
                logger.warn("Connection status: ", wlan_status.get(wstatus, f"UNKNOWN WLAN STATUS {wstatus}" ))
                logger.warn('Waiting for connection...', count)
                pin.toggle()
                time.sleep(1)
                count -= 1
                
            else:
                ip = wlan.ifconfig()[0]
                logger.info("Connected",ip,"to WiFi")
                break

        pin.low()

        # If not connected   
        if not connected:
            
            # Wait a bit then try again
            logger.warn("Will retry wifi in", wifi_retry, minutes[wifi_retry != 1])
            for i in range(10):
                pin.toggle()
                time.sleep(.1)
            pin.low()
            time.sleep(wifi_retry * 60)

logger.init()
connect_to_wifi(2,("minute","minutes"))
from machine import Pin
import network
import constants
import logger

# Connect to WiFi
def connect_to_wifi():
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
            if not connected:
                logger.info('Waiting for connection...', count)
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
            

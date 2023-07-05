"""
A simple example that connects to the MQTT server and publishes
a JSON string of sensed temperature, pressure and humidity
"""
print("Starting")
from weather import WEATHER
import network
import time
from umqtt.simple import MQTTClient
import constants
import errno
import ujson
from machine import Pin
from read_vsys import read_vsys

# Interval between measurements / retrys (minutes)
interval = 1
wifi_retry = 1

# MQTT details
mqtt_publish_topic = "/weather"

def wifi_available():
    """ Check if network is available"""
    test = False
    for ap in wlan.scan():
        test = ap[0].decode("ascii") == constants.ssid
#        print(test, ap[0].decode("ascii") , constants.ssid)
        if test:
            break;
 
    return test

# Loop infinitely
while True:
        
    # Connect to WiFi
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
                print('Waiting for connection...', count)
                pin.toggle()
                time.sleep(1)
                count -= 1
                
            else:
                ip = wlan.ifconfig()[0]
                print("Connected to",ip,"on WiFi")
                break

        pin.low()

        # If not connected   
        if not connected:
            
            # Wait a bit then try again
            print("Will retry wifi in", wifi_retry,"minutes")
            for i in range(10):
                pin.toggle()
                time.sleep(.1)
            pin.low()
            time.sleep(wifi_retry * 60)
     
    # Proceed to getting data
    
    try:
        # Set up call to weather sensor
        weather = WEATHER()

        #mqtt_client = MQTTClient(
        #        client_id=mqtt_client_id,
        #        server=mqtt_host,
        #        user=mqtt_username,
        #        password=mqtt_password)
        # Initialize the MQTTClient 

        mqtt_client = MQTTClient(
            client_id = constants.mqtt_client_id,
            server = constants.mqtt_host,
            port = 1883)

        # Connect to the MQTT server
        mqtt_client.connect()
        
        while True:

            # Get weather readings in dictionary form
            raw=weather.get_readings()
            
            # Convert to JSON format
            payload = ujson.dumps(raw)
            
            # Publish the data
            print("Publish", payload)
            mqtt_client.publish(mqtt_publish_topic, payload)
            
            # Publish aux data
            vsys = str(read_vsys())
            print("Publish vsys", vsys)
            mqtt_client.publish("/voltage", vsys)

            # Delay before next reading
            time.sleep(interval * 60)
            
    except Exception as e:
        print(f'Exception: {e}')

        print("Will attempt reconnect in",wifi_retry,"minutes")
        time.sleep(wifi_retry * 60)


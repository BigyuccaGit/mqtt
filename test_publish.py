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
interval = 15
wifi_retry = 5

# MQTT details
mqtt_publish_topic = "/weather"

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
                print('Waiting for connection...', count)
                pin.toggle()
                time.sleep(1)
                count -= 1
                
            else:
                ip = wlan.ifconfig()[0]
                print("Connected",ip,"to WiFi")
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


def connect_to_mqtt_server():
    """ setup client and connect to mqtt server """
    
    #mqtt_client = MQTTClient(
    #        client_id=mqtt_client_id,
    #        server=mqtt_host,
    #        user=mqtt_username,
    #        password=mqtt_password)
    # Initialize the MQTTClient 

    print("Setting up mqtt client")
    mqtt_client = MQTTClient(
        client_id = constants.mqtt_client_id,
        server = constants.mqtt_host,
        port = 1883)

    # Connect to the MQTT server
    print("Connecting to mqtt_client")
    mqtt_client.connect()
    
    return mqtt_client
        
        
# Loop infinitely
while True:
 
    try: 
        # Connect to WiFi
        connect_to_wifi()
        
        # Set up call to weather sensor
        weather = WEATHER()

        # Setup client connection to mqtt server 
        mqtt_client = connect_to_mqtt_server()
        
        # Commence loop over readings
        while True:
            # Get weather readings in dictionary form
            raw=weather.get_readings()
            # Convert to JSON format
            payload = ujson.dumps(raw)            
            # Publish the data
            print("Publish weather", payload)
            mqtt_client.publish(mqtt_publish_topic, payload)
            
            # Publish aux data
            vsys = str(read_vsys())
            print("Publish vsys", vsys, "volts")
            mqtt_client.publish("/voltage", vsys)

            # Delay before next reading
            print("Next sample in",interval,"minutes")
            time.sleep(interval * 60)
            
    except Exception as e:
        print(f'Exception: {e}')

        print("Will attempt to reconnect in",wifi_retry,"minutes")
        time.sleep(wifi_retry * 60)


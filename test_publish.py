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

# Connect to WiFi
pin=Pin("LED", Pin.OUT)
pin.high()
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(constants.ssid, constants.password)
while wlan.isconnected() == False:
    print('Waiting for connection...')
    pin.toggle()
    time.sleep(1)
print("Connected to WiFi")
pin.low()

# MQTT details
mqtt_publish_topic = "/weather"

# Set up call to sensor
weather = WEATHER()

# Initialize our MQTTClient 
#mqtt_client = MQTTClient(
#        client_id=mqtt_client_id,
#        server=mqtt_host,
#        user=mqtt_username,
#        password=mqtt_password)

mqtt_client = MQTTClient(
        client_id = constants.mqtt_client_id,
        server = constants.mqtt_host,
        port = 1883)

# Connect to the MQTT server
try:
    mqtt_client.connect()
except OSError as exc:
    print(exc.errno)
    print(errno.errorcode[exc.errno])

# Interval between measurements (minutes)
interval = 15

try:
    while True:

        # Get weather readings in dictionary form
        raw=weather.get_readings()
        
        # Convert to JSON format
        payload = ujson.dumps(raw)
        
        # Publish the data
        print("Publish ", payload)
        mqtt_client.publish(mqtt_publish_topic, payload)

        # Delay before next reading
        time.sleep(interval * 60)
        
except Exception as e:
    print(f'Failed to publish message: {e}')
finally:
    mqtt_client.disconnect()
"""
A simple example that connects to the Adafruit IO MQTT server
and publishes values that represent a sine wave
"""
print("Starting")
import network
import time
from math import sin
from umqtt.simple import MQTTClient
from secret import *
import errno
import ujson

# Fill in your WiFi network name (ssid) and password here:
wifi_ssid = ssid
wifi_password = password

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wifi_ssid, wifi_password)
while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(1)
print("Connected to WiFi")

# Fill in your Adafruit IO Authentication and Feed MQTT Topic details
#mqtt_host = "io.adafruit.com"
mqtt_host = "192.168.1.193"
mqtt_username = "bigyucca"  # Your Adafruit IO username
mqtt_password = "aio_tsUF15Gzlh9Ythcv9RlwnngXbTXh"  # Adafruit IO Key
#mqtt_publish_topic = "bigyucca/feeds/my-data-feed"  # The MQTT topic for your Adafruit IO Feed
#mqtt_publish_topic = "/test"
mqtt_publish_topic = "/testjson"

# Enter a random ID for this MQTT Client
# It needs to be globally unique across all of Adafruit IO.
mqtt_client_id = "1234567890"

# Initialize our MQTTClient and connect to the MQTT server
#mqtt_client = MQTTClient(
#        client_id=mqtt_client_id,
#        server=mqtt_host,
#        user=mqtt_username,
#        password=mqtt_password)

mqtt_client = MQTTClient(
        client_id=mqtt_client_id,
        server=mqtt_host,
        port = 1883)

try:
    mqtt_client.connect()
except OSError as exc:
    print(exc.errno)
    print(errno.errorcode[exc.errno])

# Publish a data point to the Adafruit IO MQTT server every 3 seconds
# Note: Adafruit IO has rate limits in place, every 3 seconds is frequent
#  enough to see data in realtime without exceeding the rate limit.
counter = 0
try:
    while True:
        
        # Generate some dummy data that changes every loop
        sine = sin(counter)
        counter += .8
 
        payload={"timestamp": time.time()}
        payload["V1"] = sine
        payload["V2"] = sine * 2
        payload["V3"] = sine * 3
        
        js = ujson.dumps(payload)
        
        # Publish the data to the topic!
#        print(f'Publish {sine:.2f}')
#        mqtt_client.publish(mqtt_publish_topic, str(sine))
        print("Publish ", js)
        mqtt_client.publish(mqtt_publish_topic, js)
        # Delay a bit to avoid hitting the rate limit
        time.sleep(3)
except Exception as e:
    print(f'Failed to publish message: {e}')
finally:
    mqtt_client.disconnect()
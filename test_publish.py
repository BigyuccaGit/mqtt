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
import sys

# Interval between measurements / retrys (minutes)
interval = 15
wifi_retry = 5

# MQTT details
mqtt_publish_topic = "/weather"

class ForceRestart(Exception):
    """ Raised to force restart"""
    pass

class NoAck(Exception):
    """ Raised to force restart"""
    pass
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
            

def mqtt_subscription_callback(topic, message):
    """ So that we can respond to messages on an MQTT topic, we need a callback
        function that will handle the messages."""
    global interval
    global callback
    global ack_received
    global payload
    
    # Flag that callback happened
    callback = True
    
    # Now process the subcription message
    message_s = message.decode("utf-8")
    print (f'Topic \"{topic.decode("utf-8")}\" received message \"{message_s}\"')  # Debug print out of what was received over MQTT

    if topic == b'/weather_ack':
        ack_received = message_s.replace(" ","") == payload.replace(" ","")
        print("ACK", ack_received, message_s.replace(" ",""), payload.replace(" ",""))
        
    elif topic == b'exit':
        sys.exit()
    
    elif topic == b'interval':
        interval=float(message)
        
    elif topic == b'restart':
        raise ForceRestart
    
def process_callbacks():
    """ Process callbacks"""
    while True:
        callback = False
        mqtt_client.check_msg()
        if not callback:
            break
        
def connect_to_mqtt_server():
    """ Setup client and connect to mqtt server """
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
    
    # Before connecting, tell the MQTT client to use the callback
    print("Setting up call back")
    mqtt_client.set_callback(mqtt_subscription_callback)
    
    # Connect to the MQTT server
    print("Connecting to mqtt_client")
    mqtt_client.connect()
    
    return mqtt_client
        
# Loop infinitely
while True:
    
    """ Main loop"""
    
    global callback
    global payload
    global ack_received
     
    payload=""

    try: 

        # Connect to WiFi
        connect_to_wifi()
        
        # Set up call to weather sensor
        weather = WEATHER()

        # Setup client connection to mqtt server 
        mqtt_client = connect_to_mqtt_server()
        
         # Once connected, subscribe to the MQTT topic
        print("Subcribing")
        mqtt_client.subscribe("exit")
        mqtt_client.subscribe("interval")
        mqtt_client.subscribe("restart")
        mqtt_client.subscribe("/weather_ack")
        
        print("Wait 1 second to settle")
        time.sleep(1)
        
        # Commence loop over readings
        print("Commence reading loop")
        while True:
            
            # Check if any messages are waiting in q and pass all of them to the callback
            process_callbacks()
           
            # Get weather readings in dictionary form
            raw=weather.get_readings()
            # Convert to JSON format
            payload = ujson.dumps(raw)            
            # Publish the data
            print("Publish weather", payload)
            mqtt_client.publish(mqtt_publish_topic, payload)
            
            # Allow time for ACK
            time.sleep(1)
            
            # Look for ack
            process_callbacks()
            
            # Force retry if no ack
            print("ack_received", ack_received)
            if not ack_received:
                raise NoAck
                 
            # Publish aux data
            vsys = str(read_vsys())
            print("Publish vsys", vsys, "volts")
            mqtt_client.publish("/voltage", vsys)

            # Delay before next reading
            print("Next sample in",interval,"minutes")
            time.sleep(interval * 60)#   
           
    except ForceRestart as e:
        print(f'Exception: {e}')
        print("Will attempt to reconnect")       

    except Exception as e:
        print(f'Exception: {repr(e)}')

        print("Will attempt to reconnect in",wifi_retry,"minutes")
        time.sleep(wifi_retry * 60)


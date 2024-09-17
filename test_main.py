"""
Connects to the MQTT server and publishes a JSON string 
of sensed temperature, pressure and humidity

Micropython doc
https://docs.micropython.org/en/latest/

MQTT doc
https://pypi.org/project/micropython-umqtt.simple/

"""
import logger
# Ensure logger exists
logger.init()
logger.info("Starting ===================================")
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
import ntptime_picow
from oserror import errortext
import os
from median_filter import MEDIAN_FILTER as MDF
import network
from ota import OTAUpdater

# Interval between measurements / retrys (minutes)
interval = 2
wifi_retry = 2

# Other intervals
ack_delay = 2 # N.B. seconds

# Define various exceptions
class ForceRestart(Exception):
    """ Raised to force restart"""
    pass

class ForceExit(Exception):
    """ Raised to force exit"""
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
            

def mqtt_subscription_callback(topic, message):
    """ So that we can respond to messages on an MQTT topic, we need a callback
        function that will handle the messages."""

    global ack_valid
    
    # Flag that callback happened
    callback = True
    
    # Now process the subscription message
    message_s = message.decode("utf-8")
    logger.info(f'Topic \"{topic.decode("utf-8")}\", message \"{message_s}\"')  # Debug print out of what was received over MQTT

    if topic == b'/weather_ack':
        ack_valid = message_s.replace(" ","") == payload.replace(" ","")

        if ack_valid:
            logger.info("ACK", ack_valid, payload.replace(" ",""))
        else:
            logger.info("ACK invalid: sub message = ", message_s.replace(" ",""))               
            logger.info("ACK invalid: payload = ", payload.replace(" ",""))               
        
    elif topic == b'exit':
        raise ForceExit
    
    elif topic == b'interval':
        interval=float(message)
        
    elif topic == b'restart':
        raise ForceRestart
    
    elif topic == b'ota':
        logger.info("OTA command received")
        
        repo_url = "https://github.com/BigyuccaGit/mqtt/"#"https://github.com/kevinmcaleer/ota_test/main/"
        ota_updater = OTAUpdater(repo_url)
        ota_updater.loop_over_updates()
        
    else:
        logger.error(f"Unknown topic {topic} received")
    
def process_callbacks(mqtt_client):
    
    """ Process callbacks"""
    while True:
        callback = False
        
        # Check for server pending subscription messages, if present pass to callback
        mqtt_client.check_msg()
        
        # If no messages present, exit
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

    logger.info("Setting up mqtt client")
    mqtt_client = MQTTClient(
        client_id = constants.mqtt_client_id,
        server = constants.mqtt_host,
        port = 1883)
    
    # Before connecting, tell the MQTT client to use the callback
    logger.info("Setting up call back")
    mqtt_client.set_callback(mqtt_subscription_callback)
    
    # Connect to the MQTT server
    logger.info("Connecting to mqtt_client")
    mqtt_client.connect()
    
    return mqtt_client

# Publish to mqtt_server
def publish_loop(mqtt_client, weather):
    
    global payload

    discard = True
    
    while True:
        
        # Check if any messages are waiting in q and pass all of them to the callback
        process_callbacks(mqtt_client)
       
        # Get weather readings in dictionary form (discarding 1st reading)
        if discard:
            logger.info("Discarding 1st set of readings")
            raw=weather.get_readings()
            time.sleep(1)
            discard = False
            
        raw=weather.get_readings()   
        
        # Perform low pass filtering and add
        raw['T_FILTER'] = t_filter.calc(raw["Temperature"])
        raw['P_FILTER'] = p_filter.calc(raw["Pressure"])
        raw['H_FILTER'] = h_filter.calc(raw["Humidity %"])

        # Convert to JSON format
        payload = ujson.dumps(raw)
        
        # Publish the data
        logger.info("Publish weather", payload)
        mqtt_client.publish(mqtt_publish_topic, payload)
        
        # Allow time for ACK
        time.sleep(ack_delay)
        
        # Look for ack
        process_callbacks(mqtt_client)
        
        # Force retry if no ack
        logger.info("ack_valid", ack_valid)
        if not ack_valid:
            raise NoAck(payload)
        else:
            # Send all of log
            for line in logger.iterate():
                mqtt_client.publish("/pico_log", line)
            # Then clear it
            logger.clear()
             
        # Publish aux data
        vsys = read_vsys()
        light = ldr.read_u16() * conv
        v_filt = v_filter.calc(vsys)
        l_filt = l_filter.calc(light)
        aux = {"Voltage": vsys, "Light" : light, "V_FILTER": v_filt, "L_FILTER": l_filt}
        payload = ujson.dumps(aux) 
        logger.info("Publish vsys & light", vsys, light, "volts", payload)
        mqtt_client.publish("/auxiliary", payload)

        # Delay before next reading
        logger.info("Next sample in",interval,minutes[interval != 1])
        time.sleep(interval * 60)
        
                      
# The main loop
def main_loop():
    
    # Loop infinitely 
    while True:
        
        # Setup mqtt server, wi-fi, weather sensor and NTP
        try: 
            # Set up call to weather sensor
            logger.info("Setting up weather sensor")
            weather = WEATHER()

            time.sleep(1)

            # Connect to WiFi
            connect_to_wifi()
            
            # Get NTP time
            ntptime_picow.settime()
            
            # Setup client connection to mqtt server 
            mqtt_client = connect_to_mqtt_server()
            
             # Once connected, subscribe to the MQTT topic
            logger.info("subscribing")
            mqtt_client.subscribe("exit")
            mqtt_client.subscribe("interval")
            mqtt_client.subscribe("restart")
            mqtt_client.subscribe("ota")
            mqtt_client.subscribe("/weather_ack")
            
            logger.info("Wait 1 second to settle")
            time.sleep(1)
            
            # Commence loop over readings
            logger.info("Commence reading loop")
            
            # Loop over getting weather readings and publishing
            publish_loop(mqtt_client, weather)
           
        except ForceRestart as e:
            logger.error(f'ForceRestart Exception: {e} {repr(e)}')
            logger.error("Will attempt to reconnect")
            
        except OSError as e:
            logger.error(f'OSError: {e} -> {errortext[e.errno]}')
      #      logger.error(f'OSError: {e}')

            logger.error("Will attempt to reconnect in",wifi_retry,minutes[wifi_retry != 1])
            time.sleep(wifi_retry * 60)
            
        except ForceExit as e:
            logger.error(f'Force Exit Exception: {e} {repr(e)}')
            raise KeyboardInterrupt
        
        except NoAck as e:
            logger.error(f'NoAck Exception: {repr(e)}')

            logger.error("Will attempt to reconnect in",wifi_retry,minutes[wifi_retry != 1])
            time.sleep(wifi_retry * 60)
        
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt
            
        except Exception as e:
            logger.error(f'Unanticipated Exception: {e} {repr(e)}')
            logger.error("Will attempt to reconnect in",wifi_retry, minutes[wifi_retry != 1])
            time.sleep(wifi_retry * 60)

# Finally, start running code

# MQTT details
mqtt_publish_topic = "/weather"

# Creat low pass filtering instances
v_filter = MDF()
l_filter = MDF()
t_filter = MDF()
p_filter = MDF()
h_filter = MDF()

# Light dependent resistor and conversion factor
ldr = machine.ADC(28)
conv = 3.3/65535.0

minutes=("minute","minutes") # Single/plural
            
main_loop()


    


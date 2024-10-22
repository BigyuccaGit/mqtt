"""
Connects to the MQTT server and publishes a JSON string 
of sensed temperature, pressure and humidity

Micropython doc
https://docs.micropython.org/en/latest/

MQTT doc
https://pypi.org/project/micropython-umqtt.simple/

"""
import machine
import logger
# Ensure logger exists
logger.init()
logger.info("Starting ===================================")
from weather import WEATHER
import time
from umqtt.simple import MQTTClient
import constants
import errno
import ujson
from machine import Timer
from read_vsys import read_vsys
import sys
import ntptime_picow
from oserror import errortext
import os
from median_filter import MEDIAN_FILTER as MDF
import network
from ota import OTAUpdater
from picotemp import picotemp
from connect_to_wifi import connect_to_wifi

# Interval between measurements / retrys (minutes)
interval = 15
wifi_retry = 2

# Poll interval looking for subscriptions (seconds)
subscription_period = 5 

# Define various exceptions
class ForceRestart(Exception):
    """ Raised to force restart"""
    pass

class ForceExit(Exception):
    """ Raised to force exit"""
    pass

# Left in for diagnostics
def poll_for_subscriptions(timer):
    
        print("polling")
        global mqtt_client

        # If found, call subscription callback
        mqtt_client.check_msg()

""" Handle subscription callbacks"""
def mqtt_subscription_callback(topic, message):
     
    global interval
    global mqtt_client
    global timer

    # Now process the subscription message
    message_s = message.decode("utf-8")
    logger.info(f'Topic \"{topic.decode("utf-8")}\", message \"{message_s}\"')  # Debug print out of what was received over MQTT
    
    if topic == b'exit':
        raise ForceExit
    
    elif topic == b'interval':
        interval=float(message)
        print("Processed interval ------------", interval)
    
    elif topic == b'sub_poll':
        print(message)
        subscription_period = float(message)
        timer.deinit()
        timer.init(period = int(1000*subscription_period), callback =  lambda timer : mqtt_client.check_msg())
#        timer.init(period = int(1000*subscription_period), callback =  poll_for_subscriptions)
        print("Processed sub_poll ------------", subscription_period)
        
    elif topic == b'restart':
        raise ForceRestart
    
    elif topic == b'ota':
        logger.info("OTA command received")
        
        repo_url = "https://github.com/BigyuccaGit/mqtt/"#"https://github.com/kevinmcaleer/ota_test/main/"
        ota_updater = OTAUpdater(repo_url)
        ota_updater.loop_over_updates()
        
    else:
        logger.error(f"Unknown topic {topic} received")
  
""" Setup client and connect to mqtt server """
def connect_to_mqtt_server():
    
    # Initialize the MQTTClient 

    logger.info("Setting up mqtt client")
    mqtt_client = MQTTClient(
        client_id = constants.mqtt_client_id,
        server = constants.mqtt_host,
    #        user=mqtt_username,
    #        password=mqtt_password)
        port = 1883)
    
    # Before connecting, tell the MQTT client to use the callback function
    logger.info("Setting up subscriptions callback")
    mqtt_client.set_callback(mqtt_subscription_callback)
    
    # Connect to the MQTT server
    logger.info("Connecting to mqtt_client")
    mqtt_client.connect()
    
    return mqtt_client

# Publish to mqtt_server
def publish_loop(mqtt_client, weather):

    discard = True
    
    while True:
               
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
        mqtt_client.publish(mqtt_publish_topic, payload, qos = 1)
  
        # Publish aux data
        vsys = read_vsys()
        light = ldr.read_u16() * conv
        pico_temp = picotemp()

        v_filt = v_filter.calc(vsys)
        l_filt = l_filter.calc(light)
        pico_temp_filt = picotemp_filter.calc(pico_temp)
        
        aux = {"Voltage": vsys, "Light" : light, "Picotemp" : pico_temp,
               "V_FILTER": v_filt, "L_FILTER": l_filt, "PICO_TEMP" : pico_temp_filt}
        payload = ujson.dumps(aux)
        
        logger.info("Publish auxiliary data", payload)
        mqtt_client.publish("/auxiliary", payload, qos = 1)
        
        # Announce delay before next reading
        logger.info("Next sample in",interval,minutes[interval != 1])

        # Send all of log
        for line in logger.iterate():
            mqtt_client.publish("/pico_log", line, qos = 1)
        # Then clear it
        logger.clear()
  
        # Delay
        time.sleep(interval * 60)
                            
# The main loop
def main_loop():
    
    global timer
    global mqtt_client
    
    # Loop infinitely 
    while True:
        
        # Setup mqtt server, wi-fi, weather sensor and NTP
        try: 
            # Set up call to weather sensor
            logger.info("Setting up weather sensor")
            weather = WEATHER()

            time.sleep(1)

            # Connect to WiFi
            connect_to_wifi(wifi_retry, minutes)
            
            # Get NTP time
            ntptime_picow.settime()
            
            # Setup client connection to mqtt server 
            mqtt_client = connect_to_mqtt_server()
            
             # Once connected, subscribe to the MQTT topics
            logger.info("Subscribing")
            mqtt_client.subscribe("exit")
            mqtt_client.subscribe("interval")
            mqtt_client.subscribe("sub_poll")
            mqtt_client.subscribe("restart")
            mqtt_client.subscribe("ota")
            mqtt_client.subscribe("/weather_ack")
            
            logger.info("Wait 1 second to settle")
            time.sleep(1)
            
            # Start polling for subscriptions
            logger.info("Start polling for subscriptions every", 1000*subscription_period, "ms")
            timer = Timer()
            timer.init(period = 1000*subscription_period, callback =  lambda timer : mqtt_client.check_msg())
#            timer.init(period = int(1000*subscription_period), callback = poll_for_subscriptions)

            # Commence loop over readings
            logger.info("Commence publishing loop")
            
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
   
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt
            
        except Exception as e:
            logger.error(f'Unanticipated Exception: {e} {repr(e)}')
            logger.error("Will attempt to reconnect in",wifi_retry, minutes[wifi_retry != 1])
            time.sleep(wifi_retry * 60)

# Finally, start running code

# MQTT detailsc
mqtt_publish_topic = "/weather"

# Create low pass filtering instances
v_filter = MDF()
l_filter = MDF()
t_filter = MDF()
p_filter = MDF()
h_filter = MDF()
picotemp_filter = MDF()

# Light dependent resistor and conversion factor
ldr = machine.ADC(28)
conv = 3.3/65535.0

minutes=("minute","minutes") # Single/plural
            
main_loop()


    


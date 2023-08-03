"""
A simple example that connects to the MQTT server and publishes
a JSON string of sensed temperature, pressure and humidity
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
from low_pass_filter import LOW_PASS_FILTER as LPF

# Interval between measurements / retrys (minutes)
interval = 0.2
wifi_retry = 5

# Low pass filtering
v_lpf = LPF()
l_lpf = LPF()
t_lpf = LPF()
p_lpf = LPF()
h_lpf = LPF()

# MQTT details
mqtt_publish_topic = "/weather"

ldr = machine.ADC(28)
conv = 3.3/65535.0

class ForceRestart(Exception):
    """ Raised to force restart"""
    pass

class ForceExit(Exception):
    """ Raised to force exit"""
    pass

class NoAck(Exception):
    """ Raised to force restart"""
    pass
import network
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
            logger.warn("Will retry wifi in", wifi_retry,"minutes")
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
    global ack_valid
    global payload
    
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
            logger.info("ACK", ack_valid, message_s.replace(" ",""), payload.replace(" ",""))               
        
    elif topic == b'exit':
        raise ForceExit
    
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
        
# Loop infinitely
while True:
    
    """ Main loop"""
    
    global callback
    global payload
    global ack_valid
     
    payload=""
    
    # Set up call to weather sensor
    logger.info("Setting up weather sensor")
    weather = WEATHER()
    
    try: 

  #      os.mkdir("dummydir")
        
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
        mqtt_client.subscribe("/weather_ack")
        
        logger.info("Wait 1 second to settle")
        time.sleep(1)
        
        # Commence loop over readings
        logger.info("Commence reading loop")
        while True:
            
            # Check if any messages are waiting in q and pass all of them to the callback
            process_callbacks()
           
            # Get weather readings in dictionary form
            raw=weather.get_readings()
            
            # Perform low pass filtering and add
            raw['T_LPF'] = t_lpf.calc(raw["Temperature"])
            raw['P_LPF'] = p_lpf.calc(raw["Pressure"])
            raw['H_LPF'] = h_lpf.calc(raw["Humidity %"])
 
            # Convert to JSON format
            payload = ujson.dumps(raw)            
            # Publish the data
            logger.info("Publish weather", payload)
            mqtt_client.publish(mqtt_publish_topic, payload)
            
            # Allow time for ACK
            time.sleep(1)
            
            # Look for ack
            process_callbacks()
            
            # Force retry if no ack
            logger.info("ack_valid", ack_valid)
            if not ack_valid:
                raise NoAck
            else:
                for line in logger.iterate():
                    mqtt_client.publish("/pico_log", line)
                logger.clear()
                 
            # Publish aux data
            vsys = read_vsys()
            light = ldr.read_u16() * conv
            v_filt = v_lpf.calc(vsys)
            l_filt = l_lpf.calc(light)
            aux = {"Voltage": vsys, "Light" : light, "V_LPF": v_filt, "L_LPF": l_filt}
            payload = ujson.dumps(aux) 
            logger.info("Publish vsys & light", vsys, light, "volts", payload)
            mqtt_client.publish("/auxiliary", payload)

            # Delay before next reading
            logger.info("Next sample in",interval,"minutes")
            time.sleep(interval * 60)#   
           
    except ForceRestart as e:
        logger.error(f'Exception: {e}')
        logger.error("Will attempt to reconnect")
        
    except OSError as e:
        logger.error(f'OSError: {e} -> {errortext[e.errno]}')
  #      logger.error(f'OSError: {e}')

        logger.error("Will attempt to reconnect in",wifi_retry,"minutes")
        time.sleep(wifi_retry * 60)
        
    except ForceExit as e:
        logger.error(f'Exception: {e}')
        raise KeyboardInterrupt
    
    except KeyboardInterrupt as e:
        raise KeyboardInterrupt
        
    except Exception as e:
        logger.error(f'Unanticipated Exception: {e} {repr(e)}')

        logger.error("Will attempt to reconnect in",wifi_retry,"minutes")
        time.sleep(wifi_retry * 60)


    


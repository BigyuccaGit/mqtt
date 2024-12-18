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
import ntptime_picow as ntp
from oserror import errortext
import os
from median_filter import MEDIAN_FILTER as MDF
import network
from ota import OTAUpdater
from picotemp import picotemp
from connect_to_wifi import connect_to_wifi
import saverestore as dct

# Get parameters
params = dct.restore()

# Interval between measurements / retrys (minutes)
interval : int = params["interval"] #15

wifi_retry : int = params["wifi_retry"] #2

# Poll interval looking for subscriptions (seconds)
sub_poll : int = params["sub_poll"] #5

# Interval between drift corrections using NTP (hrs)
drift_correction : int = params["drift_correction"] # 24

# Default quality of service
qos : int = params["qos"] # 1

# Daylight threshold (volts)
daylight_threshold = params["daylight_threshold"]

# Low Voltage threshold (volts)
voltage_threshold = params["voltage_threshold"]

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
        logger.info("Forcing exit")
        raise ForceExit
    
    elif topic == b'interval':
        interval=int(message)
        params["interval"] = interval
        logger.info("Processed interval ------------", interval)
    
    elif topic == b'sub_poll':
        sub_poll = int(message)
        timer.deinit()
        timer.init(period = int(1000*sub_poll), callback =  lambda timer : mqtt_client.check_msg())
#        timer.init(period = int(1000*subscription_period), callback =  poll_for_subscriptions)
        params["sub_poll"] = sub_poll
        logger.info("Processed sub_poll ------------", sub_poll)
        
    elif topic == b'restart':
        logger.info("Forcing restart")
        raise ForceRestart
    
    elif topic == b'ota':
        logger.info("OTA command received")
        
        repo_url = "https://github.com/BigyuccaGit/mqtt/"#"https://github.com/kevinmcaleer/ota_test/main/"
        ota_updater = OTAUpdater(repo_url)
        ota_updater.loop_over_updates()

    elif topic == b'qos':
        qos = int(message)
        params["qos"] = qos
        logger.info("Processed qos ------------", qos) 

    elif topic == b'drift_correction':
        drift_correction = int(message)  
        params["drift_correction"] =  drift_correction
        logger.info("Processed drift_correction interval ----- ", drift_correction)    

    elif topic == b'wifi_retry':
        wifi_retry = int(message)
        params["wifi_retry"] = wifi_retry
        logger.info("Wifi retry interval (mins) ----- ", wifi_retry)

    elif topic == b'daylight_threshold':
        daylight_threshold = float(message)  
        params["daylight_threshold"] =  daylight_threshold
        logger.info("Processed daylight threshold ----- ", daylight_threshold)  

    elif topic == b'voltage_threshold':
        voltage_threshold = float(message)  
        params["voltage_threshold"] =  voltage_threshold
        logger.info("Processed voltage threshold ----- ", voltage_threshold)    

    else:
        logger.error(f"Unknown topic {topic} received")
  
    # Save any changes
    dct.save(params)

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
    mqtt_client.publish("/connected", "", qos = qos)
    
    return mqtt_client

# Publish to mqtt_server
def publish_loop(mqtt_client, weather, last_ntp_setting):

    discard = True
    
    while True:
               
        # Get weather readings in dictionary form (discarding 1st reading)
        if discard:
            logger.info("Discarding 1st set of readings")
            raw=weather.get_readings()
            time.sleep(1)
            discard = False
            
        raw=weather.get_readings()   
        
        # Perform low pass filtering and add to dictionary
        raw['T_FILTER'] = t_filter.calc(raw["Temperature"])
        raw['P_FILTER'] = p_filter.calc(raw["Pressure"])
        raw['H_FILTER'] = h_filter.calc(raw["Humidity %"])
  
        # Get aux data
        vsys = read_vsys() 
        light = ldr.read_u16() * conv
        pico_temp = picotemp()

        # Get derived values
        daylight =  1 if (light >= daylight_threshold) else 0
        low_voltage = 0 if vsys >= voltage_threshold else 1

        v_filt = v_filter.calc(vsys)
        l_filt = l_filter.calc(light)
        pico_temp_filt = picotemp_filter.calc(pico_temp)

           # Convert raw weather data to JSON format
        weather_payload = ujson.dumps(raw)
        
        # Determine qos level
        qos_level = qos if daylight else 0

        # Publish the weather data
        logger.info("Publish weather", weather_payload)
        mqtt_client.publish(mqtt_publish_topic, weather_payload, qos = qos_level)
    
        # Convert aux data to JSON format
        aux = {"Voltage": vsys, "Light" : light, "Picotemp" : pico_temp,
               "V_FILTER": v_filt, "L_FILTER": l_filt, "PICO_TEMP" : pico_temp_filt,
               "DAYLIGHT": daylight}
        aux_payload = ujson.dumps(aux)
        
        logger.info("Publish auxiliary data", aux_payload)
        mqtt_client.publish("/auxiliary", aux_payload, qos = qos_level)
               
        # Announce delay before next reading
        this_interval = interval if not low_voltage else 2 * interval
        y,m,d,h,min,s,_,_ = time.gmtime(time.time() + this_interval * 60)
        logger.info("Next sample in", this_interval, f"{minutes[interval != 1]} @ {y}/{m:02d}/{d:02d} {h:02d}:{min:02d}:{s:02d}Z")

        # Send all of log
        for line in logger.iterate():
            mqtt_client.publish("/pico_log", line, qos = qos_level)
        # Then clear it
        logger.clear()
  
        # Delay
        time.sleep(this_interval * 60)
        
         # Perform time drift correction if required
        tdif = time.time() - last_ntp_setting
        
#        print("DEBUG", tdif, drift_correction_interval_hrs * 3600, tdif + last_ntp_setting, last_ntp_setting )
        if tdif >= drift_correction * 3600:
            ntp_time = ntp.gettime()
            if ntp_time != 0:
                ntp.setRTC(ntp_time)
                last_ntp_setting = time.time()
            else:
                logger.info("NTP time reset failed")
                
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
            ntp.settime()
            last_ntp_setting = time.time()
            logger.info(f"Time will be checked for drift every {drift_correction} hrs")
            
            # Setup client connection to mqtt server 
            mqtt_client = connect_to_mqtt_server()
            
             # Once connected, subscribe to the MQTT topics
            logger.info("Subscribing")
            topics = ("exit", "interval", "sub_poll", "restart", "ota", "qos",
                       "drift_correction", "wifi_retry", "daylight_threshold", "voltage_threshold")
            for topic in topics:
                mqtt_client.subscribe(topic)
            
            logger.info("Wait 1 second to settle")
            time.sleep(1)
            
            # Start polling for subscriptions
            logger.info("Start polling for subscriptions every", 1000 * sub_poll, "ms")
            timer = Timer()
            timer.init(period = 1000 * sub_poll, callback =  lambda timer : mqtt_client.check_msg())
#            timer.init(period = int(1000 * sub_poll), callback = poll_for_subscriptions)
                    
            # Commence loop over readings
            logger.info("Commence publishing loop")
  
            # Loop over getting weather readings and publishing
            publish_loop(mqtt_client, weather, last_ntp_setting)
           
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


    


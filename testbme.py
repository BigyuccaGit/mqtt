import bme
import time
import ujson

bme280=bme.BME280()

timestamp=1


while True:
    payload={
    "timestamp": timestamp,
    }
    raw=bme280.get_data()
    print(type(raw), raw)
    for key,val in raw.items():
        payload[key]=val
       
    js = ujson.dumps(payload)
    print(type(js), js)
    time.sleep(1)
    timestamp += 1
    

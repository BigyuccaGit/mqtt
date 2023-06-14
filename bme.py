import bme280
from machine import I2C, Pin

class BME280:
    def __init__(self, sda = 14, scl = 15, freq = 400000):
        self.i2c=I2C(1, sda=Pin(sda), scl=Pin(scl), freq=freq)
        self.bme = bme280.BME280(i2c=self.i2c)
        
# Read data from sensor
    def get_data(self):
    
        t, p, h = self.bme.read_compensated_data()
 
        t /= 100
        p /= 25600
        h /= 1024
        
        measurements={}
        measurements["T"] = t
        measurements["P"] = p
        measurements["H"] = h
        
        return measurements
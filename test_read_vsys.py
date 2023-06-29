import machine
import sys
import time
from measure_vsys import measure_vsys

# def measure_vsys():
#     Pin(25, Pin.OUT, value=1)
#     Pin(29, Pin.IN, pull=None)
#     reading = machine.ADC(3).read_u16() * 9.9 / 2**16
#     Pin(25, Pin.OUT, value=0, pull=Pin.PULL_DOWN)
#     Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
#     return reading

while True:
    r= measure_vsys()
    print(f"VSYS {round(r,1)} {r}")
    time.sleep(2)

# print("sys.implementation:{}".format(sys.implementation))
# print("sys.version:{}".format(sys.version))
# wl_cs = machine.Pin(25) # WiFi chip SDIO_DATA3 / gate on FET between VSYS divider (FET drain) and GPIO29 (FET source)
# print("Initial WL_CS (GPIO25) state:{}".format(wl_cs))
# wl_cs.init(mode=machine.Pin.OUT, value=1)
# pin = machine.ADC(29)
# adc_reading  = pin.read_u16()
# adc_voltage  = (adc_reading * 3.3) / 65535
# vsys_voltage = adc_voltage * 3
# print("""ADC reading:{}
# ADC voltage:{}
# VSYS voltage:{}""".format(adc_reading, adc_voltage, vsys_voltage))
# wl_cs.init(mode=machine.Pin.ALT, pull=machine.Pin.PULL_DOWN, alt=31)#try to restore initial WL_CS state




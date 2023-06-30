""" Reads VSYS on Pico W

Taken from

https://forums.raspberrypi.com/viewtopic.php?p=2062543&hilit=ADC+29#p2062568 """

from machine import Pin, ADC

def read_vsys():
    Pin(25, Pin.OUT, value=1)
    Pin(29, Pin.IN, pull=None)
    reading = ADC(3).read_u16() * 9.9 / 2**16
    Pin(29, Pin.ALT, Pin.PULL_DOWN, alt=7)
    Pin(25, Pin.OUT, value=0, pull=Pin.PULL_DOWN)
    return reading

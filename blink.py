from machine import Pin
from time import sleep

pin=Pin("LED",Pin.OUT)
print("Hello")       
while True:
    pin.toggle()
    sleep(1)
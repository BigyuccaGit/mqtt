from machine import Pin
from time import sleep
       
pin=Pin("LED",Pin.OUT)
print("Hello")
print("Hello Again")       
while True:
    pin.toggle()
    sleep(1)
import machine
import utime

chg = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
pgood = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
pin=machine.Pin("LED",machine.Pin.OUT)

i=0
while True:
    i+=1
    print(f"{i}, chg = {chg.value()}, pgood = {pgood.value()}")
    pin.toggle()
    utime.sleep(2)

import machine
import utime

chg = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)
pgood = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

while True:
    print(f"chg = {chg.value()}, pgood = {pgood.value()}")
    utime.sleep(2)
    
from machine import Timer, WDT
import time

print("Starting")
def mycallback(t):
    print("Call back")
    dir(t)
    wdt.feed()
    pass

wdt = WDT(timeout = 8388)

tim = Timer()
tim.init(mode=tim.PERIODIC, freq = 1/8.0, callback = lambda cb: wdt.feed())

#tim2 = Timer()
#tim2.init(mode=tim.PERIODIC, freq = 1/2.0, callback = mycallback)

loop = 1
while True:
    print("Alive", loop)
    time.sleep(2)
    loop += 1
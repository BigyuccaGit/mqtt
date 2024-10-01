from utime import sleep
from pitemp import pitemp

while True:
    print(pitemp())
    sleep(2)
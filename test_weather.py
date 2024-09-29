from weather import WEATHER
from time import sleep

weather=WEATHER()

while True:
     raw=weather.get_readings()
     print(raw)
     sleep(2)
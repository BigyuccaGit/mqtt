from low_pass_filter import LOW_PASS_FILTER as LPF
import math
import time
import random

lpf = LPF(0.85)

angle = 0.0
while True:
    
    data = math.sin(angle  * math.pi/180.0) + random.randrange(-1, 1) *0.1
    data = 1 + random.gauss(0, 0.2)
    result = lpf.calc(data)
    
    print("DATA", data, 'LPF', result)
    
    time.sleep(.2)
    
    angle += 2
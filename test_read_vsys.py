print("Starting")
import machine
import sys
import time
from read_vsys import read_vsys

while True:
    r= read_vsys()
    print(f"VSYS {round(r,1)} {r}")
    time.sleep(2)






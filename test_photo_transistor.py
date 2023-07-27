print("Starting")
import machine
import utime

photo = machine.ADC(28)

conversion_factor = 3.3/65535.0

while True:
    v_photo = photo.read_u16() * conversion_factor
  #  v_resist = resist.read_u16() * conversion_factor
    
    print(v_photo)
    
    utime.sleep(2)
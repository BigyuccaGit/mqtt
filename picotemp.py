import machine

def picotemp():
    sensor_reading = machine.ADC(4)

    conv_factor = 3.3/(65535)

    reading = sensor_reading.read_u16() * conv_factor

    return 27 - (reading - 0.706)/0.001721


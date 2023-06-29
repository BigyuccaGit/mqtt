import machine

def measure_vsys():
    machine.Pin(25, machine.Pin.OUT, value=1)
    machine.Pin(29, machine.Pin.IN, pull=None)
    reading = machine.ADC(3).read_u16() * 9.9 / 2**16
    machine.Pin(25, machine.Pin.OUT, value=0, pull=machine.Pin.PULL_DOWN)
    machine.Pin(29, machine.Pin.ALT, pull=machine.Pin.PULL_DOWN, alt=7)
    return reading

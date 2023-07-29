# Adapted from official ntptime by Peter Hinch July 2022
# The main aim is portability:
# Detects host device's epoch and returns time relative to that.
# Basic approach to local time: add offset in hours relative to UTC.
# Timeouts return a time of 0. These happen: caller should check for this.
# Replace socket timeout with select.poll as per docs:
# http://docs.micropython.org/en/latest/library/socket.html#socket.socket.settimeout
 
import socket
import struct
import select
from time import gmtime
import errno
import machine
import time
from time import sleep
import logger

# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
# (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600 if gmtime(0)[0] == 2000 else 2208988800

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"
#host='ntp.plus.net'
def gettime(hrs_offset=0):  # Local time offset in hrs relative to UTC
#    print("debug 1")
    
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
#    print("debug 2")
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
    except OSError:
        return 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    poller = select.poll()
    poller.register(s, select.POLLIN)
    try:
        s.sendto(NTP_QUERY, addr)
        if poller.poll(1000):  # time in milliseconds
            msg = s.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]  # Can return 0
            return max(val - NTP_DELTA + hrs_offset * 3600, 0)
    except OSError as exc:
        print(errno.errorcode[exc.errno])


        #pass  # LAN error
    finally:
        s.close()
    return 0  # Timeout or LAN error occurred

def settime(hrs_offset=0):
    while True:
        logger.info("Trying to get NTP time")
        time_ntp = gettime()
        if time_ntp != 0:
            break
        else:
            logger.warn("Timout obtaining NTP time, retrying ...")
            sleep(1.0)
     
    year, month, mday, hour, minute, second, _, _ = time.localtime(time_ntp)
    machine.RTC().datetime((year, month, mday, 0, hour + hrs_offset, minute,second,0))
    logger.info("Time set to {0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(year, month, mday, hour + hrs_offset, minute,second))

# sunrise/sunset api - scruss, 2022-09
# partly nicked from https://github.com/Lukaspy/ESP8266-Sunset-Sunrise-Relay/blob/master/main.py

import time, urequests
from connect_to_wifi import connect_to_wifi


last_dayno = -1
# count = 0
LAT = 51.0293158  
LONG = -0.3957787
def api_suntimes(time0):

    global last_dayno #, count
    
    
    gmtime = time.gmtime(time0)
    if gmtime[7] != last_dayno:
#        print("Change in dayno", gmtime[7], last_dayno, count)
#        count = 0
        date = f"{gmtime[0]}-{gmtime[1]}-{gmtime[2]}"
#        print(time0, date)
        r = urequests.get(f"https://api.sunrise-sunset.org/json?lat={LAT}&lng={LONG}&formatted=0&date={date}").json()
#    print(r)
        if r["status"] == "OK":
            last_dayno = gmtime[7]
            return r['results']
        else:
            return None
#    else:
#        count += 1
        
    return None

#ntptime.settime()
#print("Time is: ", time.localtime())
#for d in range(1,31):
#    suntimes = api_suntimes(time.mktime((2024,11,d,0,0,0,0,0)))
#t=time.gmtime(0)
#print(d, suntimes["sunrise"], suntimes["sunset"])
#td=time.mktime((2024,11,1,0,0,0,0,0))

minutes=("minute", "minutes")

connect_to_wifi(1, minutes)

ts=time.time()
for i in range(ts, ts + 365*24*3600, 15*60):
 #   print(i)
    suntimes = api_suntimes(i)
    if suntimes != None:
      #  gmtime = time.gmtime(i)
      #  date=f"{gmtime[0]}-{gmtime[1]}-{gmtime[2]}"
        print(suntimes["sunrise"], suntimes["sunset"])     
        
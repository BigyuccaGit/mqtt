import dictionary

d={"interval":15, 
   "sub_poll":5,
   "qos":1,
   "drift_correction":24,
   "wifi_retry":2}


dictionary.save(d)

dx = dictionary.restore()

print(dx)

print(dx == d)

for x in dx:
    print(x, dx[x])
import dictionary

d={"Z":1, "Y":2}

filename =  "json.buffer"
dictionary.save(d, filename)

dx = dictionary.restore(filename)

print(dx)

print(dx == d)
print(dx["Z"])
print(dx["Y"])

print(dictionary.restore(filename)["Z"])
print(dictionary.restore(filename)["Y"])
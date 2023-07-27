import os,time

size = 0
try:
    #while True:
    with open("size_test.txt", "w") as f:
        pass
    
    for i in range(0,10):
        with open("size_test.txt", "a") as f:
            f.write("1234567890" * 8 + '\n')
#          size = os.stat("size_text.txt")[6]
        size += 8*10 +1
        print("size", size)
except Exception as e:
    print(f'Exception: {repr(e)}')

with open("size_test.txt", "r") as f:
    count = 0
    for line in f:
        count += 1
        print(count,line.strip("\n"))
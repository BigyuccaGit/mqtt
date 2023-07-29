import machine, gc, os, time

_logfile_ = "logfile.txt"
def file(logfile):
    global _logfile_
    _logfile_ = logfile
    
def log(level, text):
#    dt = machine.RTC().datetime()
    dt = time.gmtime()
 #   datetime = "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*dt)
    datetime = "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*dt)
    log_entry = "{0} [{1:7} /{2:>8}] {3} {4}".format(datetime, level, gc.mem_free(), text,  os.stat(_logfile_)[6])
    print(log_entry, len(log_entry)+1)
    with open(_logfile_, "a") as f:
        f.write(log_entry + '\n')

def info(*items):
    log("info", " ".join(map(str, items)))

def warn(*items):
    log("warning", " ".join(map(str, items)))

def error(*items):
    log("error", " ".join(map(str, items)))

def debug(*items):
    log("debug", " ".join(map(str, items)))
    
def clear():
    with open(_logfile_, "w") as f:
        pass
        
def iterate():
    with open(_logfile_, "r") as f:
        for line in f:
            yield line.strip("\n")
        
   
        
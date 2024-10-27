import machine, gc, os, time

no_records = 0
_logfile_ = "logfile.txt"
def file(logfile):
    global _logfile_
    _logfile_ = logfile
    
def log(level, text):
    global no_records
#    dt = machine.RTC().datetime()
    no_records += 1
    dt = time.gmtime()
 #   datetime = "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*dt)
    datetime = "{0:04d}/{1:02d}/{2:02d} {3:02d}:{4:02d}:{5:02d}Z".format(*dt)
    start_size = os.stat(_logfile_)[6]
    log_entry_part1 = "{0} [{1:7} /{2:>8}] {3}".format(datetime, level, gc.mem_free(), text)
    end_size = start_size + len(log_entry_part1) + 2*6 + 5 + 1
#    log_entry = "{0} [{1:7} /{2:>8}] {3} {5} {5}".format(datetime, level, gc.mem_free(), text,  start_size, end_size)
    log_entry = log_entry_part1 + "{0:6}{1:6}{2:5}".format(start_size, end_size, no_records)
    print(log_entry)
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
    global no_records
    no_records = 0
    with open(_logfile_, "w") as f:
        pass
        
def iterate():
    with open(_logfile_, "r") as f:
        for line in f:
            yield line.strip("\n")
            
def exists():
    return _logfile_ in os.listdir()

def init():
    if exists():
        info(f"Log file '{_logfile_}' exists")
        start_size = os.stat(_logfile_)[6]
        if start_size >= 10000:
            clear()
            error(f"Cleared log file as too big = {start_size}!")
        return
    else:
        clear()
        info(f"Created empty log file: {_logfile_}")
        
   
        

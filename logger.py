import machine, gc, os
class LOGGER:
    
    def __init__(self, logfile = "logfile.txt"):
        self.logfile = logfile
        
    def log(self, level, text):
        dt = machine.RTC().datetime()
        datetime = "{0:04d}-{1:02d}-{2:02d} {4:02d}:{5:02d}:{6:02d}".format(*dt)
        log_entry = "{0} [{1:7} /{2:>8}] {3} {4}".format(datetime, level, gc.mem_free(), text,  os.stat(self.logfile)[6])
        print(log_entry, len(log_entry)+1)
        with open(self.logfile, "a") as f:
            f.write(log_entry + '\n')

    def info(self, *items):
        self.log("info", " ".join(map(str, items)))

    def warn(self, *items):
        self.log("warning", " ".join(map(str, items)))

    def error(self, *items):
        self.log("error", " ".join(map(str, items)))

    def debug(self, *items):
        self.log("debug", " ".join(map(str, items)))
        
    def clear(self):
        with open(self.logfile, "w") as f:
            pass
        
    def iterate(self):
        with open(self.logfile, "r") as f:
            for line in f:
                yield line.strip("\n")
        
   
        
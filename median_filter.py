class MEDIAN_FILTER:
    def __init__(self, size = 3):
        self.size = size
        self.odd = (self.size % 2) == 1
        self.pointer = 0
        self.buffer = self.size * [None]
        self.mid_point = self.size//2 # What about even size
        self.buffer_full = False
        
    def calc(self, current_value):
        
        self.buffer[self.pointer] = current_value
        self.pointer = (self.pointer + 1) % self.size
        if not self.buffer_full:
            
            self.buffer_full = self.pointer == (self.size - 1)
            
            return current_value
        
        _buffer_copy = self.buffer.copy()
        _buffer_copy.sort()
        
        if self.odd:
            return _buffer_copy[self.mid_point]
        else:
            return (_buffer_copy[self.mid_point] + _buffer_copy[self.mid_point-1])/2.0


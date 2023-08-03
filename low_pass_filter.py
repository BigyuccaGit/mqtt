class LOW_PASS_FILTER:
    def __init__(self, alpha = 0.85):
        self.first = True
        self.current_value_weight = 1 - alpha
        self.previous_value_weight = alpha
        self.previous = 0.0
        
    def calc(self, current_value):
        
        if self.first:
            self.first = False
            result = current_value
        else:
            result = current_value * self.current_value_weight + self.previous * self.previous_value_weight
            
        self.previous = result
        return result


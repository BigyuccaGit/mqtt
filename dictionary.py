import json

def save(d,filename):
    with open(filename, 'w') as f:
        json.dump(d, f)
        
def restore(filename):
    with open(filename) as f:
        result=json.load(f)
        
    return result
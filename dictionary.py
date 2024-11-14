import json

filename =  "parameters.json"

def save(d):
    with open(filename, 'w') as f:
        json.dump(d, f)
        
def restore():
    with open(filename) as f:
        result=json.load(f)
        
    return result
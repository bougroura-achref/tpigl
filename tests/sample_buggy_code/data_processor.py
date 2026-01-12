"""
Sample Buggy Code #2 - Data Processor
This file contains intentional code quality issues for testing The Refactoring Swarm.

Issues include:
- Unused variables
- Magic numbers
- Missing docstrings
- Poor error handling
- Inconsistent formatting
"""

import json
import os

data={"name":"test","value":42}
x=10
y=20
z=30

def load_data(filepath):
    f=open(filepath,'r')
    content=f.read()
    f.close()
    return json.loads(content)

def save_data(filepath,data):
    f=open(filepath,'w')
    f.write(json.dumps(data))
    f.close()

def process_items(items):
    result=[]
    for i in items:
        if i>100:
            result.append(i*0.5)
        elif i>50:
            result.append(i*0.75)
        else:
            result.append(i)
    return result

class DataProcessor:
    def __init__(self):
        self.data=None
        self.processed=False
        self.config={"max":100,"min":0,"threshold":50}
    
    def load(self,path):
        try:
            self.data=load_data(path)
            return True
        except:
            return False
    
    def process(self):
        if self.data==None:
            return None
        result=[]
        for key in self.data:
            value=self.data[key]
            if isinstance(value,int) or isinstance(value,float):
                if value>self.config["threshold"]:
                    result.append(value*2)
                else:
                    result.append(value)
        self.processed=True
        return result
    
    def save(self,path):
        if self.processed==False:
            return False
        try:
            save_data(path,self.data)
            return True
        except:
            return False

def main():
    dp=DataProcessor()
    dp.load("data.json")
    result=dp.process()
    dp.save("output.json")

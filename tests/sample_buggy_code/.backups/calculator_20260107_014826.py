"""
Sample Buggy Code #1 - Calculator Module
This file contains intentional code quality issues for testing The Refactoring Swarm.

Issues include:
- Missing docstrings
- Unused imports
- Poor variable naming
- Missing type hints
- Line too long
- Bare except clauses
"""

import os
import sys
import json
import random

def add(a,b):
    return a+b

def subtract(a,b):
    return a-b

def multiply(a,b):
    return a*b

def divide(a,b):
    try:
        return a/b
    except:
        return None

class calculator:
    def __init__(self):
        self.result=0
        self.x=0
        self.y=0
    
    def set_values(self,a,b):
        self.x=a
        self.y=b
    
    def add_values(self):
        self.result=self.x+self.y
        return self.result
    
    def subtract_values(self):
        self.result=self.x-self.y
        return self.result
    
    def multiply_values(self):
        self.result=self.x*self.y
        return self.result
    
    def divide_values(self):
        try:
            self.result=self.x/self.y
        except:
            self.result=None
        return self.result
    
    def calculate_complex_expression_with_very_long_method_name_that_exceeds_line_length_limits(self,a,b,c,d):
        return (a+b)*(c-d)/(a*b+c*d)

def process_data(data):
    result=[]
    for i in range(len(data)):
        item=data[i]
        if item>0:
            result.append(item*2)
        elif item<0:
            result.append(item*-1)
        else:
            result.append(0)
    return result

l=[1,2,3,4,5]
r=process_data(l)

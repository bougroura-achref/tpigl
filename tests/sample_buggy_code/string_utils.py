"""
Sample Buggy Code #3 - String Utilities
This file contains intentional code quality issues for testing The Refactoring Swarm.

Issues include:
- No type hints
- Missing docstrings on functions
- Code duplication
- Inefficient string operations
- Bare except
"""

import re
import string

def reverse_string(s):
    result=""
    for i in range(len(s)-1,-1,-1):
        result=result+s[i]
    return result

def count_vowels(s):
    count=0
    for c in s:
        if c=='a' or c=='e' or c=='i' or c=='o' or c=='u':
            count=count+1
        if c=='A' or c=='E' or c=='I' or c=='O' or c=='U':
            count=count+1
    return count

def count_consonants(s):
    count=0
    vowels="aeiouAEIOU"
    for c in s:
        if c.isalpha() and c not in vowels:
            count=count+1
    return count

def is_palindrome(s):
    s=s.lower()
    s=re.sub('[^a-z]','',s)
    reversed_s=reverse_string(s)
    if s==reversed_s:
        return True
    else:
        return False

def capitalize_words(s):
    words=s.split(' ')
    result=[]
    for word in words:
        if len(word)>0:
            new_word=word[0].upper()+word[1:]
            result.append(new_word)
    return ' '.join(result)

def remove_duplicates(s):
    seen=[]
    result=""
    for c in s:
        if c not in seen:
            seen.append(c)
            result=result+c
    return result

class StringProcessor:
    def __init__(self,text):
        self.text=text
        self.processed=False
    
    def process(self):
        self.text=self.text.strip()
        self.processed=True
    
    def get_stats(self):
        return {"length":len(self.text),"vowels":count_vowels(self.text),"consonants":count_consonants(self.text)}
    
    def transform(self,operation):
        if operation=="reverse":
            return reverse_string(self.text)
        elif operation=="upper":
            return self.text.upper()
        elif operation=="lower":
            return self.text.lower()
        elif operation=="capitalize":
            return capitalize_words(self.text)
        else:
            return self.text

if __name__=="__main__":
    sp=StringProcessor("Hello World")
    sp.process()
    print(sp.get_stats())
    print(sp.transform("reverse"))

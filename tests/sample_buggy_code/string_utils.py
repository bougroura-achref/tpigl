"""
String Utilities Module.

This module provides common string manipulation functions and a StringProcessor class.
"""

import re
from typing import Dict, List, Set, Union

def reverse_string(s: str) -> str:
    """Return the reversed string."""
    return s[::-1]

def count_vowels(s: str) -> int:
    """Return the count of vowels in the string."""
    vowels = "aeiouAEIOU"
    return sum(1 for c in s if c in vowels)

def count_consonants(s: str) -> int:
    """Return the count of consonants in the string."""
    vowels = "aeiouAEIOU"
    return sum(1 for c in s if c.isalpha() and c not in vowels)

def is_palindrome(s: str) -> bool:
    """Check if the string is a palindrome (ignoring casing and non-alphabetic chars)."""
    s_clean = re.sub(r'[^a-zA-Z]', '', s).lower()
    return s_clean == s_clean[::-1]

def capitalize_words(s: str) -> str:
    """Capitalize each word in the string."""
    return ' '.join(word.capitalize() for word in s.split())

def remove_duplicates(s: str) -> str:
    """Remove duplicate characters while maintaining order."""
    seen: Set[str] = set()
    result: List[str] = []
    for c in s:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return "".join(result)

class StringProcessor:
    """Class to store and manipulate a text string."""
    
    def __init__(self, text: str) -> None:
        """Initialize with text."""
        self.text: str = text
        self.processed: bool = False
    
    def process(self) -> None:
        """Process the text (strip whitespace)."""
        self.text = self.text.strip()
        self.processed = True
    
    def get_stats(self) -> Dict[str, int]:
        """Return statistics about the text."""
        return {
            "length": len(self.text),
            "vowels": count_vowels(self.text),
            "consonants": count_consonants(self.text)
        }
    
    def transform(self, operation: str) -> str:
        """
        Transform the text based on the operation.
        
        Supported operations: 'reverse', 'upper', 'lower', 'capitalize'.
        """
        if operation == "reverse":
            return reverse_string(self.text)
        elif operation == "upper":
            return self.text.upper()
        elif operation == "lower":
            return self.text.lower()
        elif operation == "capitalize":
            return capitalize_words(self.text)
        else:
            return self.text

if __name__ == "__main__":
    sp = StringProcessor("Hello World")
    sp.process()
    print(sp.get_stats())
    print(sp.transform("reverse"))

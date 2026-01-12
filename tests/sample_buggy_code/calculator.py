"""
Calculator Module.

This module provides basic arithmetic operations and a Calculator class.
"""

from typing import Optional, Union

Number = Union[int, float]

def add(a: Number, b: Number) -> Number:
    """Add two numbers."""
    return a + b

def subtract(a: Number, b: Number) -> Number:
    """Subtract b from a."""
    return a - b

def multiply(a: Number, b: Number) -> Number:
    """Multiply two numbers."""
    return a * b

def divide(a: Number, b: Number) -> Optional[float]:
    """
    Divide a by b.
    
    Returns None if b is zero.
    """
    try:
        return a / b
    except ZeroDivisionError:
        return None

class Calculator:
    """A simple calculator class to store and manipulate a pair of values."""
    
    def __init__(self) -> None:
        """Initialize the Calculator."""
        self.result: Number = 0
        self.x: Number = 0
        self.y: Number = 0
    
    def set_values(self, a: Number, b: Number) -> None:
        """Set the values for operation."""
        self.x = a
        self.y = b
    
    def add_values(self) -> Number:
        """Add the stored values."""
        self.result = self.x + self.y
        return self.result
    
    def subtract_values(self) -> Number:
        """Subtract the stored values."""
        self.result = self.x - self.y
        return self.result

"""Calculator Module.

This module provides basic arithmetic operations and a Calculator class.
"""

from typing import Union, Optional

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """Add two numbers.
    
    Args:
        a: First number to add
        b: Second number to add
        
    Returns:
        The sum of a and b
        
    Raises:
        TypeError: If inputs are not numbers
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """Subtract b from a.
    
    Args:
        a: Number to subtract from
        b: Number to subtract
        
    Returns:
        The difference of a and b
        
    Raises:
        TypeError: If inputs are not numbers
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """Multiply two numbers.
    
    Args:
        a: First number to multiply
        b: Second number to multiply
        
    Returns:
        The product of a and b
        
    Raises:
        TypeError: If inputs are not numbers
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a * b


def divide(a: Number, b: Number) -> Number:
    """Divide a by b.
    
    Args:
        a: Dividend (number to be divided)
        b: Divisor (number to divide by)
        
    Returns:
        The quotient of a divided by b
        
    Raises:
        ZeroDivisionError: If b is zero
        TypeError: If inputs are not numbers
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


class Calculator:
    """A simple calculator class to store and manipulate a pair of values.
    
    This class provides methods for basic arithmetic operations on two
    stored values, utilizing the standalone arithmetic functions for
    consistency and maintainability.
    """
    
    def __init__(self) -> None:
        """Initialize the Calculator with default values.
        
        Sets result, x, and y to 0.
        """
        self.result: Number = 0
        self.x: Number = 0
        self.y: Number = 0
    
    def set_values(self, a: Number, b: Number) -> None:
        """Set the values for operation.
        
        Args:
            a: First value to store
            b: Second value to store
            
        Raises:
            TypeError: If inputs are not numbers
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Both values must be numbers")
        self.x = a
        self.y = b
    
    def add_values(self) -> Number:
        """Add the stored values using the standalone add function.
        
        Returns:
            The sum of self.x and self.y, also stored in self.result
        """
        self.result = add(self.x, self.y)
        return self.result
    
    def subtract_values(self) -> Number:
        """Subtract the stored values using the standalone subtract function.
        
        Returns:
            The difference of self.x and self.y, also stored in self.result
        """
        self.result = subtract(self.x, self.y)
        return self.result
    
    def multiply_values(self) -> Number:
        """Multiply the stored values using the standalone multiply function.
        
        Returns:
            The product of self.x and self.y, also stored in self.result
        """
        self.result = multiply(self.x, self.y)
        return self.result
    
    def divide_values(self) -> Number:
        """Divide the stored values using the standalone divide function.
        
        Returns:
            The quotient of self.x divided by self.y, also stored in self.result
            
        Raises:
            ZeroDivisionError: If self.y is zero
        """
        self.result = divide(self.x, self.y)
        return self.result
    
    def get_result(self) -> Number:
        """Get the current result value.
        
        Returns:
            The current value stored in self.result
        """
        return self.result
    
    def clear(self) -> None:
        """Reset all values to zero.
        
        Sets result, x, and y back to their initial state of 0.
        """
        self.result = 0
        self.x = 0
        self.y = 0
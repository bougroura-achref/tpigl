"""Module for basic arithmetic operations.

This module provides simple mathematical functions for performing
basic arithmetic calculations.
"""


def calculate_sum(a: float, b: float) -> float:
    """Calculate the sum of two numbers.
    
    Args:
        a (float): The first number to add.
        b (float): The second number to add.
    
    Returns:
        float: The sum of a and b.
    
    Example:
        >>> calculate_sum(2.0, 3.0)
        5.0
        >>> calculate_sum(1.5, 2.5)
        4.0
    """
    return a + b


if __name__ == "__main__":
    import doctest
    doctest.testmod()

"""Module containing utility functions for number validation."""

from typing import Union

# Maximum threshold value for validation
MAX_THRESHOLD: int = 10


def is_valid_positive_number(number: Union[int, float]) -> bool:
    """Check if a number is positive and within valid range.
    
    Args:
        number: The number to validate (int or float)
        
    Returns:
        bool: True if number is positive and less than 100, False otherwise
        
    Examples:
        >>> is_valid_positive_number(50)
        True
        >>> is_valid_positive_number(-5)
        False
        >>> is_valid_positive_number(150)
        False
    """
    return 0 < number < 100

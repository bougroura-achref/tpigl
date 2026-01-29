"""Calculator Module.

This module provides basic arithmetic operations and a Calculator class
with comprehensive error handling and validation.
"""

from typing import Union

Number = Union[int, float]


class CalculatorError(Exception):
    """Base exception class for calculator-related errors."""
    pass


class InvalidInputError(CalculatorError):
    """Raised when invalid input is provided to calculator operations."""
    pass


def validate_number(value, name: str = "value") -> None:
    """Validate that a value is a number.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        
    Raises:
        InvalidInputError: If value is not a number
    """
    if not isinstance(value, (int, float)):
        raise InvalidInputError(f"{name} must be a number, got {type(value).__name__}")
    if isinstance(value, bool):  # bool is subclass of int, but we don't want it
        raise InvalidInputError(f"{name} must be a number, not boolean")


def validate_numbers(first: Number, second: Number) -> None:
    """Validate that both arguments are numbers.
    
    Args:
        first: First number to validate
        second: Second number to validate
        
    Raises:
        InvalidInputError: If either argument is not a number
    """
    validate_number(first, "first argument")
    validate_number(second, "second argument")


def add(first_number: Number, second_number: Number) -> Number:
    """Add two numbers.
    
    Args:
        first_number: First number to add
        second_number: Second number to add
        
    Returns:
        The sum of first_number and second_number
        
    Raises:
        InvalidInputError: If inputs are not numbers
    """
    validate_numbers(first_number, second_number)
    return first_number + second_number


def subtract(first_number: Number, second_number: Number) -> Number:
    """Subtract second_number from first_number.
    
    Args:
        first_number: Number to subtract from
        second_number: Number to subtract
        
    Returns:
        The difference of first_number and second_number
        
    Raises:
        InvalidInputError: If inputs are not numbers
    """
    validate_numbers(first_number, second_number)
    return first_number - second_number


def multiply(first_number: Number, second_number: Number) -> Number:
    """Multiply two numbers.
    
    Args:
        first_number: First number to multiply
        second_number: Second number to multiply
        
    Returns:
        The product of first_number and second_number
        
    Raises:
        InvalidInputError: If inputs are not numbers
    """
    validate_numbers(first_number, second_number)
    return first_number * second_number


def divide(dividend: Number, divisor: Number) -> Number:
    """Divide dividend by divisor.
    
    Args:
        dividend: Number to be divided
        divisor: Number to divide by
        
    Returns:
        The quotient of dividend divided by divisor
        
    Raises:
        ZeroDivisionError: If divisor is zero
        InvalidInputError: If inputs are not numbers
    """
    validate_numbers(dividend, divisor)
    
    if divisor == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    
    return dividend / divisor


class Calculator:
    """A calculator class for basic arithmetic operations.
    
    This class provides methods for basic arithmetic operations on two
    stored values, utilizing the standalone arithmetic functions for
    consistency and maintainability.
    
    Attributes:
        result: The result of the last operation
        first_value: First operand value
        second_value: Second operand value
    """
    
    def __init__(self, first_value: Number = 0, second_value: Number = 0) -> None:
        """Initialize the Calculator with optional initial values.
        
        Args:
            first_value: Initial first value (default: 0)
            second_value: Initial second value (default: 0)
            
        Raises:
            InvalidInputError: If initial values are not numbers
        """
        self._result: Number = 0
        self._first_value: Number = 0
        self._second_value: Number = 0
        
        if first_value != 0 or second_value != 0:
            self.set_values(first_value, second_value)
    
    @property
    def result(self) -> Number:
        """Get the current result value.
        
        Returns:
            The current value stored in result
        """
        return self._result
    
    @property
    def first_value(self) -> Number:
        """Get the first value.
        
        Returns:
            The current first value
        """
        return self._first_value
    
    @property
    def second_value(self) -> Number:
        """Get the second value.
        
        Returns:
            The current second value
        """
        return self._second_value
    
    def set_values(self, first_val: Number, second_val: Number) -> None:
        """Set the values for operation.
        
        Args:
            first_val: First value to store
            second_val: Second value to store
            
        Raises:
            InvalidInputError: If inputs are not numbers
        """
        validate_numbers(first_val, second_val)
        self._first_value = first_val
        self._second_value = second_val
    
    def add_values(self) -> Number:
        """Add the stored values using the standalone add function.
        
        Returns:
            The sum of stored values, also stored in result
        """
        self._result = add(self._first_value, self._second_value)
        return self._result
    
    def subtract_values(self) -> Number:
        """Subtract stored values using the standalone subtract function.
        
        Returns:
            The difference of stored values, also stored in result
        """
        self._result = subtract(self._first_value, self._second_value)
        return self._result
    
    def multiply_values(self) -> Number:
        """Multiply stored values using the standalone multiply function.
        
        Returns:
            The product of stored values, also stored in result
        """
        self._result = multiply(self._first_value, self._second_value)
        return self._result
    
    def divide_values(self) -> Number:
        """Divide stored values using the standalone divide function.
        
        Returns:
            The quotient of stored values, also stored in result
            
        Raises:
            ZeroDivisionError: If second_value is zero
        """
        self._result = divide(self._first_value, self._second_value)
        return self._result
    
    def get_result(self) -> Number:
        """Get the current result value.
        
        Returns:
            The current value stored in result
            
        Note:
            This method is deprecated. Use the result property instead.
        """
        return self._result
    
    def clear(self) -> None:
        """Reset all values to zero.
        
        Sets result, first_value, and second_value back to 0.
        """
        self._result = 0
        self._first_value = 0
        self._second_value = 0
    
    def __str__(self) -> str:
        """Return string representation of calculator state.
        
        Returns:
            String showing current values and result
        """
        return (f"Calculator(first_value={self._first_value}, "
                f"second_value={self._second_value}, result={self._result})")
    
    def __repr__(self) -> str:
        """Return detailed string representation for debugging.
        
        Returns:
            Detailed string representation of the calculator
        """
        return (f"Calculator(first_value={self._first_value}, "
                f"second_value={self._second_value}, "
                f"result={self._result})")
    
    def __eq__(self, other) -> bool:
        """Check equality with another Calculator instance.
        
        Args:
            other: Another Calculator instance to compare with
            
        Returns:
            True if both calculators have the same values, False otherwise
        """
        if not isinstance(other, Calculator):
            return False
        return (self._first_value == other._first_value and
                self._second_value == other._second_value and
                self._result == other._result)

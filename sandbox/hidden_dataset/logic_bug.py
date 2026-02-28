def count_down(n: int) -> None:
    """Count down from n to 1, printing each number.
    
    Args:
        n: Starting number for countdown (must be positive)
    """
    while n > 0:
        print(n)
        n -= 1  # Fixed: decrement instead of increment
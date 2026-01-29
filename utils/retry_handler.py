"""
Retry Handler - Robust retry logic for LLM API calls.
"""

import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LLMAPIError(Exception):
    """Exception raised for LLM API errors."""
    pass


class MaxRetriesExceededError(Exception):
    """Exception raised when max retries are exceeded."""
    pass


def retry_llm_call(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying LLM API calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exception types to retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if it's a non-retryable error
                    error_str = str(e).lower()
                    if any(x in error_str for x in ['invalid_api_key', 'authentication']):
                        logger.error(f"Non-retryable error: {e}")
                        raise
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed.")
            
            raise MaxRetriesExceededError(
                f"Failed after {max_attempts} attempts. Last error: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator


def retry_with_fallback(
    func: Callable[..., T],
    fallback_func: Callable[..., T],
    max_attempts: int = 3,
    *args,
    **kwargs
) -> T:
    """
    Try a function with retries, falling back to another function if all retries fail.
    
    Args:
        func: Primary function to call
        fallback_func: Fallback function if primary fails
        max_attempts: Maximum retry attempts for primary function
        *args, **kwargs: Arguments to pass to functions
        
    Returns:
        Result from either primary or fallback function
    """
    try:
        return retry_llm_call(max_attempts=max_attempts)(func)(*args, **kwargs)
    except MaxRetriesExceededError:
        logger.warning("Primary function failed, using fallback")
        return fallback_func(*args, **kwargs)

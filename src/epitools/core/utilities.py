"""
This module provides helper functions, decorators, and utilities
used throughout the EpiTools package.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from functools import wraps
import time
import warnings
import inspect
from contextlib import contextmanager
from numbers import Number


# DECORATORS

def timer(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to time
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        if elapsed > 1.0:
            print(f"{func.__name__} executed in {elapsed:.2f} seconds")
        
        return result
    
    return wrapper


def validate_input(
    validator: Optional[Callable] = None,
    **validators: Callable
) -> Callable:
    """
    Decorator to validate function inputs.
    
    Args:
        validator: General validator for all arguments
        **validators: Specific validators for named parameters
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Apply general validator if provided
            if validator:
                for name, value in bound_args.arguments.items():
                    bound_args.arguments[name] = validator(value)
            
            # Apply specific validators
            for name, validator_func in validators.items():
                if name in bound_args.arguments:
                    bound_args.arguments[name] = validator_func(
                        bound_args.arguments[name]
                    )
            
            return func(*bound_args.args, **bound_args.kwargs)
        
        return wrapper
    
    return decorator


def deprecated(version: str, replacement: Optional[str] = None) -> Callable:
    """
    Decorator to mark functions as deprecated.
    
    Args:
        version: Version when deprecated
        replacement: Replacement function name
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = f"Function '{func.__name__}' is deprecated since version {version}"
            if replacement:
                message += f". Use '{replacement}' instead."
            
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def memoize(maxsize: int = 128) -> Callable:
    """
    Simple memoization decorator.
    
    Args:
        maxsize: Maximum cache size
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = (args, frozenset(kwargs.items()))
            
            if key in cache:
                return cache[key]
            
            # Call function
            result = func(*args, **kwargs)
            
            # Manage cache size
            if len(cache) >= maxsize:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            
            cache[key] = result
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    return decorator


# DATA UTILITIES

def safe_divide(
    numerator: Union[Number, np.ndarray],
    denominator: Union[Number, np.ndarray],
    default: Any = np.nan
) -> Union[Number, np.ndarray]:
    """
    Safe division with handling of zero denominators.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Value to return when denominator is zero
        
    Returns:
        Result of division or default value
    """
    if isinstance(numerator, np.ndarray) or isinstance(denominator, np.ndarray):
        result = np.full_like(
            np.asarray(numerator), 
            default, 
            dtype=float
        )
        mask = denominator != 0
        result[mask] = numerator[mask] / denominator[mask]
        return result
    else:
        return numerator / denominator if denominator != 0 else default


def clip_values(
    values: Union[Number, np.ndarray],
    lower: Optional[float] = None,
    upper: Optional[float] = None
) -> Union[Number, np.ndarray]:
    """
    Clip values to specified bounds.
    
    Args:
        values: Values to clip
        lower: Lower bound
        upper: Upper bound
        
    Returns:
        Clipped values
    """
    if isinstance(values, np.ndarray):
        return np.clip(values, lower, upper)
    else:
        result = values
        if lower is not None:
            result = max(result, lower)
        if upper is not None:
            result = min(result, upper)
        return result


def format_number(
    value: float,
    decimals: int = 3,
    scientific: bool = False
) -> str:
    """
    Format number for display.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        scientific: Use scientific notation
        
    Returns:
        Formatted string
    """
    if np.isnan(value):
        return "NaN"
    elif np.isinf(value):
        return "Inf" if value > 0 else "-Inf"
    
    if scientific:
        return f"{value:.{decimals}e}"
    else:
        return f"{value:.{decimals}f}"


def format_pvalue(p: float) -> str:
    """
    Format p-value for display.
    
    Args:
        p: P-value
        
    Returns:
        Formatted p-value
    """
    if p < 0.001:
        return "<0.001"
    elif p > 0.999:
        return ">0.999"
    else:
        return f"{p:.3f}"


def create_bins(
    data: np.ndarray,
    n_bins: int = 10,
    method: str = "equal_width"
) -> np.ndarray:
    """
    Create bins for histogram or categorization.
    
    Args:
        data: Data to bin
        n_bins: Number of bins
        method: 'equal_width' or 'equal_frequency'
        
    Returns:
        Bin edges
    """
    data = np.asarray(data)
    data = data[~np.isnan(data)]
    
    if method == "equal_width":
        return np.linspace(np.min(data), np.max(data), n_bins + 1)
    
    elif method == "equal_frequency":
        percentiles = np.linspace(0, 100, n_bins + 1)
        return np.percentile(data, percentiles)
    
    else:
        raise ValueError(f"Unknown binning method: {method}")


# STATISTICAL UTILITIES

def logit(p: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Logit transformation.
    
    Args:
        p: Probability (0-1)
        
    Returns:
        Logit(p)
    """
    p = np.asarray(p)
    p = np.clip(p, 1e-10, 1 - 1e-10)
    return np.log(p / (1 - p))


def expit(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Expit (inverse logit) transformation.
    
    Args:
        x: Log-odds value
        
    Returns:
        Probability
    """
    x = np.asarray(x)
    return 1 / (1 + np.exp(-x))


def standardize(
    x: np.ndarray,
    ddof: int = 1
) -> np.ndarray:
    """
    Standardize array (z-score normalization).
    
    Args:
        x: Array to standardize
        ddof: Degrees of freedom for std calculation
        
    Returns:
        Standardized array
    """
    x = np.asarray(x)
    return (x - np.mean(x)) / np.std(x, ddof=ddof)


def winsorize(
    x: np.ndarray,
    limits: Tuple[float, float] = (0.05, 0.05)
) -> np.ndarray:
    """
    Winsorize array by limiting extreme values.
    
    Args:
        x: Array to winsorize
        limits: Tuple of (lower_limit, upper_limit) as proportions
        
    Returns:
        Winsorized array
    """
    x = np.asarray(x)
    lower_limit, upper_limit = limits
    
    # Calculate quantiles
    lower_q = np.quantile(x, lower_limit)
    upper_q = np.quantile(x, 1 - upper_limit)
    
    # Clip values
    return np.clip(x, lower_q, upper_q)


# CONTEXT MANAGERS

@contextmanager
def numpy_errstate(**kwargs):
    """
    Context manager for numpy error handling.
    
    Args:
        **kwargs: Numpy error state parameters
        
    Example:
        with numpy_errstate(divide='ignore', invalid='ignore'):
            result = np.divide(a, b)
    """
    old_state = np.geterr()
    np.seterr(**kwargs)
    try:
        yield
    finally:
        np.seterr(**old_state)


@contextmanager
def pandas_display_options(**kwargs):
    """
    Context manager for pandas display options.
    
    Args:
        **kwargs: Pandas display options
        
    Example:
        with pandas_display_options(max_rows=10, precision=3):
            print(df)
    """
    import pandas as pd
    original_options = {}
    
    for key, value in kwargs.items():
        if hasattr(pd, key):
            original_options[key] = getattr(pd, key)
            setattr(pd, key, value)
    
    try:
        yield
    finally:
        for key, value in original_options.items():
            setattr(pd, key, value)


# TYPE CHECKING

def is_numeric(x: Any) -> bool:
    """
    Check if value is numeric.
    
    Args:
        x: Value to check
        
    Returns:
        True if numeric
    """
    return isinstance(x, (int, float, np.number))


def is_integer_array(x: Any) -> bool:
    """
    Check if array contains only integers.
    
    Args:
        x: Array to check
        
    Returns:
        True if all values are integers
    """
    x = np.asarray(x)
    return np.issubdtype(x.dtype, np.integer)


def is_binary_array(x: Any) -> bool:
    """
    Check if array contains only binary values (0/1).
    
    Args:
        x: Array to check
        
    Returns:
        True if all values are 0 or 1
    """
    x = np.asarray(x)
    unique_vals = np.unique(x)
    return set(unique_vals).issubset({0, 1})


# FILE UTILITIES

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255 - len(ext)] + ext
    
    return sanitized


# RANDOM UTILITIES

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed
    """
    if seed is not None:
        np.random.seed(seed)
        import random
        random.seed(seed)


def generate_random_id(length: int = 8) -> str:
    """
    Generate random ID string.
    
    Args:
        length: Length of ID
        
    Returns:
        Random ID string
    """
    import random
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))
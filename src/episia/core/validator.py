"""
This module provides validation functions to ensure data quality and
prevent common errors in epidemiological calculations.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
from numbers import Number
import warnings


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_2x2_table(
    a: Any, 
    b: Any, 
    c: Any, 
    d: Any,
    allow_zero: bool = True
) -> Tuple[int, int, int, int]:
    """
    Validate 2x2 contingency table values.
    
    Args:
        a, b, c, d: Table cell values
        allow_zero: Whether zero values are allowed
        
    Returns:
        Validated integers
        
    Raises:
        ValidationError: If values are invalid
    """
    values = [a, b, c, d]
    
    for i, val in enumerate(values):
        # Check type
        if not isinstance(val, (int, np.integer)):
            try:
                values[i] = int(val)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Table cell {['a','b','c','d'][i]} must be integer, got {type(val)}"
                )
        
        # Check value range
        if values[i] < 0:
            raise ValidationError(
                f"Table cell {['a','b','c','d'][i]} must be non-negative, got {values[i]}"
            )
        
        if not allow_zero and values[i] == 0:
            raise ValidationError(
                f"Table cell {['a','b','c','d'][i]} cannot be zero"
            )
    
    return tuple(values)


def validate_proportion(
    value: Any,
    name: str = "proportion",
    allow_boundary: bool = True
) -> float:
    """
    Validate that a value is a valid proportion (0-1).
    
    Args:
        value: Value to validate
        name: Name for error messages
        allow_boundary: Whether 0 and 1 are allowed
        
    Returns:
        Validated proportion
        
    Raises:
        ValidationError: If value is invalid
    """
    try:
        p = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be numeric, got {type(value)}")
    
    if not allow_boundary:
        if not (0 < p < 1):
            raise ValidationError(f"{name} must be between 0 and 1 (exclusive), got {p}")
    else:
        if not (0 <= p <= 1):
            raise ValidationError(f"{name} must be between 0 and 1 (inclusive), got {p}")
    
    return p


def validate_confidence_level(
    confidence: Any,
    name: str = "confidence level"
) -> float:
    """
    Validate confidence level (0 < confidence < 1).
    
    Args:
        confidence: Confidence level to validate
        name: Name for error messages
        
    Returns:
        Validated confidence level
        
    Raises:
        ValidationError: If confidence is invalid
    """
    try:
        conf = float(confidence)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be numeric, got {type(confidence)}")
    
    if not (0 < conf < 1):
        raise ValidationError(f"{name} must be between 0 and 1, got {conf}")
    
    return conf


def validate_sample_size(
    n: Any,
    name: str = "sample size",
    min_size: int = 1
) -> int:
    """
    Validate sample size.
    
    Args:
        n: Sample size to validate
        name: Name for error messages
        min_size: Minimum allowed sample size
        
    Returns:
        Validated sample size
        
    Raises:
        ValidationError: If sample size is invalid
    """
    try:
        n_int = int(n)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be integer, got {type(n)}")
    
    if n_int < min_size:
        raise ValidationError(f"{name} must be at least {min_size}, got {n_int}")
    
    return n_int


def validate_dataframe(
    df: Any,
    required_columns: Optional[List[str]] = None,
    min_rows: int = 1,
    allow_nan: bool = False
) -> pd.DataFrame:
    """
    Validate pandas DataFrame for epidemiological analysis.
    
    Args:
        df: DataFrame to validate
        required_columns: Columns that must be present
        min_rows: Minimum number of rows
        allow_nan: Whether NaN values are allowed
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValidationError: If DataFrame is invalid
    """
    if not isinstance(df, pd.DataFrame):
        raise ValidationError(f"Expected pandas DataFrame, got {type(df)}")
    
    # Check minimum rows
    if len(df) < min_rows:
        raise ValidationError(f"DataFrame must have at least {min_rows} rows, got {len(df)}")
    
    # Check required columns
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValidationError(f"Missing required columns: {missing}")
    
    # Check for NaN values
    if not allow_nan and df.isna().any().any():
        nan_cols = df.columns[df.isna().any()].tolist()
        raise ValidationError(f"NaN values found in columns: {nan_cols}")
    
    return df


def validate_binary_variable(
    series: Any,
    name: str = "binary variable"
) -> pd.Series:
    """
    Validate that a series contains only binary values (0/1 or True/False).
    
    Args:
        series: Series to validate
        name: Name for error messages
        
    Returns:
        Validated series
        
    Raises:
        ValidationError: If series is invalid
    """
    if not isinstance(series, (pd.Series, np.ndarray, list)):
        raise ValidationError(f"{name} must be array-like, got {type(series)}")
    
    series = pd.Series(series)
    
    # Check for only 0/1 or True/False
    unique_values = set(series.dropna().unique())
    valid_sets = [{0, 1}, {0.0, 1.0}, {False, True}, {0, 1, True, False}]
    
    if not any(unique_values.issubset(valid_set) for valid_set in valid_sets):
        raise ValidationError(
            f"{name} must contain only binary values (0/1 or True/False), "
            f"found values: {unique_values}"
        )
    
    return series


def validate_date_series(
    dates: Any,
    name: str = "date series"
) -> pd.DatetimeIndex:
    """
    Validate date series for time series analysis.
    
    Args:
        dates: Dates to validate
        name: Name for error messages
        
    Returns:
        Validated DatetimeIndex
        
    Raises:
        ValidationError: If dates are invalid
    """
    try:
        dates_dt = pd.to_datetime(dates)
    except Exception as e:
        raise ValidationError(f"{name} could not be parsed as dates: {e}")
    
    # Check for duplicate dates
    if dates_dt.duplicated().any():
        duplicates = dates_dt[dates_dt.duplicated()].unique()
        warnings.warn(f"Duplicate dates found in {name}: {duplicates[:5]}...")
    
    # Check for sorted dates
    if not dates_dt.is_monotonic_increasing:
        warnings.warn(f"{name} is not sorted chronologically")
    
    return dates_dt


def validate_numeric_array(
    array: Any,
    name: str = "numeric array",
    min_length: int = 1,
    allow_nan: bool = False,
    allow_inf: bool = False
) -> np.ndarray:
    """
    Validate numeric array.
    
    Args:
        array: Array to validate
        name: Name for error messages
        min_length: Minimum array length
        allow_nan: Whether NaN values are allowed
        allow_inf: Whether infinite values are allowed
        
    Returns:
        Validated numpy array
        
    Raises:
        ValidationError: If array is invalid
    """
    try:
        arr = np.asarray(array, dtype=float)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be convertible to numeric array")
    
    # Check minimum length
    if len(arr) < min_length:
        raise ValidationError(f"{name} must have at least {min_length} elements, got {len(arr)}")
    
    # Check for NaN
    if not allow_nan and np.any(np.isnan(arr)):
        raise ValidationError(f"NaN values found in {name}")
    
    # Check for infinite values
    if not allow_inf and np.any(np.isinf(arr)):
        raise ValidationError(f"Infinite values found in {name}")
    
    return arr


def validate_model_parameters(
    params: Dict[str, Any],
    required_params: List[str],
    param_types: Dict[str, type]
) -> Dict[str, Any]:
    """
    Validate model parameters.
    
    Args:
        params: Parameter dictionary
        required_params: Required parameter names
        param_types: Expected types for parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValidationError: If parameters are invalid
    """
    # Check required parameters
    missing = [p for p in required_params if p not in params]
    if missing:
        raise ValidationError(f"Missing required parameters: {missing}")
    
    validated = {}
    
    for param_name, param_value in params.items():
        # Check type if specified
        if param_name in param_types:
            expected_type = param_types[param_name]
            if not isinstance(param_value, expected_type):
                # Try conversion for numeric types
                if expected_type in (int, float):
                    try:
                        param_value = expected_type(param_value)
                    except (ValueError, TypeError):
                        raise ValidationError(
                            f"Parameter '{param_name}' must be {expected_type.__name__}, "
                            f"got {type(param_value).__name__}"
                        )
                else:
                    raise ValidationError(
                        f"Parameter '{param_name}' must be {expected_type.__name__}, "
                        f"got {type(param_value).__name__}"
                    )
        
        # Additional validation based on parameter name
        if param_name.endswith('_rate') or param_name in ['beta', 'gamma', 'sigma']:
            param_value = validate_proportion(param_value, param_name)
        
        elif param_name in ['population', 'n', 'sample_size']:
            param_value = validate_sample_size(param_value, param_name)
        
        validated[param_name] = param_value
    
    return validated


def check_convergence(
    values: np.ndarray,
    tolerance: float = 1e-6,
    max_iterations: int = 1000,
    iteration: int = 0
) -> bool:
    """
    Check if iterative algorithm has converged.
    
    Args:
        values: Current values
        tolerance: Convergence tolerance
        max_iterations: Maximum allowed iterations
        iteration: Current iteration number
        
    Returns:
        True if converged
        
    Raises:
        ValidationError: If max iterations exceeded
    """
    if iteration >= max_iterations:
        raise ValidationError(
            f"Algorithm did not converge after {max_iterations} iterations"
        )
    
    # Check for NaN or infinite values
    if np.any(np.isnan(values)) or np.any(np.isinf(values)):
        return False
    
    # Simple convergence check (can be overridden)
    return True


def validate_positive(
    value: Any,
    name: str = "value",
    strict: bool = True
) -> float:
    """
    Validate that a value is positive.
    
    Args:
        value: Value to validate
        name: Name for error messages
        strict: Whether zero is allowed
        
    Returns:
        Validated positive value
        
    Raises:
        ValidationError: If value is not positive
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be numeric, got {type(value)}")
    
    if strict:
        if val <= 0:
            raise ValidationError(f"{name} must be positive, got {val}")
    else:
        if val < 0:
            raise ValidationError(f"{name} must be non-negative, got {val}")
    
    return val
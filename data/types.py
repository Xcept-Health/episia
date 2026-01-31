"""
This module provides functions for optimizing data types to reduce
memory usage while maintaining data integrity for epidemiological analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict
import warnings


def optimize_dataframe_types(
    df: pd.DataFrame,
    categorical_threshold: float = 0.5,
    downcast_integers: bool = True,
    downcast_floats: bool = True
) -> pd.DataFrame:
    """
    Optimize DataFrame column types to reduce memory usage.
    
    Args:
        df: Input DataFrame
        categorical_threshold: Maximum unique ratio for categorical conversion
        downcast_integers: Downcast integer columns
        downcast_floats: Downcast float columns
        
    Returns:
        Optimized DataFrame
    """
    df = df.copy()
    original_memory = df.memory_usage(deep=True).sum()
    
    for col in df.columns:
        df[col] = optimize_column_type(
            df[col],
            categorical_threshold=categorical_threshold,
            downcast_integers=downcast_integers,
            downcast_floats=downcast_floats
        )
    
    optimized_memory = df.memory_usage(deep=True).sum()
    reduction = ((original_memory - optimized_memory) / original_memory * 100
                if original_memory > 0 else 0)
    
    if reduction > 10:  # Only warn for significant reductions
        warnings.warn(
            f"Memory reduced by {reduction:.1f}% "
            f"({original_memory/1e6:.1f}MB -> {optimized_memory/1e6:.1f}MB)"
        )
    
    return df


def optimize_column_type(
    series: pd.Series,
    categorical_threshold: float = 0.5,
    downcast_integers: bool = True,
    downcast_floats: bool = True
) -> pd.Series:
    """
    Optimize a single column's data type.
    
    Args:
        series: Input Series
        categorical_threshold: Maximum unique ratio for categorical
        downcast_integers: Downcast integer columns
        downcast_floats: Downcast float columns
        
    Returns:
        Optimized Series
    """
    # Handle missing values
    if series.isna().all():
        return series.astype('category')
    
    # Check if already optimized
    current_type = str(series.dtype)
    if current_type.startswith('category'):
        return series
    
    # Determine optimization strategy based on data
    n_unique = series.nunique()
    n_total = len(series)
    unique_ratio = n_unique / n_total if n_total > 0 else 1.0
    
    # Convert to categorical if appropriate
    if unique_ratio < categorical_threshold and n_unique > 1:
        # For low cardinality columns
        if n_unique < 1000:  # Reasonable limit for categories
            try:
                return series.astype('category')
            except:
                pass
    
    # Optimize numeric types
    if pd.api.types.is_numeric_dtype(series):
        series = optimize_numeric_type(
            series,
            downcast_integers=downcast_integers,
            downcast_floats=downcast_floats
        )
    
    # Optimize datetime types
    elif pd.api.types.is_datetime64_any_dtype(series):
        series = optimize_datetime_type(series)
    
    # Optimize string/object types
    elif series.dtype == 'object':
        series = optimize_object_type(series)
    
    return series


def optimize_numeric_type(
    series: pd.Series,
    downcast_integers: bool = True,
    downcast_floats: bool = True
) -> pd.Series:
    """
    Optimize numeric column type.
    
    Args:
        series: Numeric Series
        downcast_integers: Downcast integer columns
        downcast_floats: Downcast float columns
        
    Returns:
        Optimized numeric Series
    """
    # Check if integer type
    is_integer = pd.api.types.is_integer_dtype(series)
    
    if is_integer and downcast_integers:
        # Downcast integers
        min_val = series.min()
        max_val = series.max()
        
        if pd.isna(min_val) or pd.isna(max_val):
            return series
        
        # Choose smallest integer type
        if min_val >= 0:
            # Unsigned integers
            if max_val <= np.iinfo(np.uint8).max:
                return series.astype(np.uint8)
            elif max_val <= np.iinfo(np.uint16).max:
                return series.astype(np.uint16)
            elif max_val <= np.iinfo(np.uint32).max:
                return series.astype(np.uint32)
        else:
            # Signed integers
            if (min_val >= np.iinfo(np.int8).min and 
                max_val <= np.iinfo(np.int8).max):
                return series.astype(np.int8)
            elif (min_val >= np.iinfo(np.int16).min and 
                  max_val <= np.iinfo(np.int16).max):
                return series.astype(np.int16)
            elif (min_val >= np.iinfo(np.int32).min and 
                  max_val <= np.iinfo(np.int32).max):
                return series.astype(np.int32)
    
    elif not is_integer and downcast_floats:
        # Downcast floats
        try:
            # Try to convert to float32 if precision is sufficient
            float32_series = series.astype(np.float32)
            if np.allclose(float32_series, series, equal_nan=True):
                return float32_series
        except:
            pass
    
    return series


def optimize_datetime_type(series: pd.Series) -> pd.Series:
    """
    Optimize datetime column type.
    
    Args:
        series: Datetime Series
        
    Returns:
        Optimized datetime Series
    """
    # Already datetime, ensure consistent type
    if series.dtype == 'datetime64[ns]':
        return series
    
    # Try to convert to datetime
    try:
        return pd.to_datetime(series)
    except:
        return series


def optimize_object_type(series: pd.Series) -> pd.Series:
    """
    Optimize object (string) column type.
    
    Args:
        series: Object Series
        
    Returns:
        Optimized Series
    """
    # Check if all values are strings
    if series.apply(lambda x: isinstance(x, str)).all():
        # Check if should be categorical
        n_unique = series.nunique()
        if n_unique / len(series) < 0.5 and n_unique < 1000:
            return series.astype('category')
    
    # Check if mixed types - try to infer
    try:
        # Try to convert to numeric
        numeric_series = pd.to_numeric(series, errors='coerce')
        if not numeric_series.isna().all():
            return optimize_numeric_type(numeric_series)
    except:
        pass
    
    try:
        # Try to convert to datetime
        datetime_series = pd.to_datetime(series, errors='coerce')
        if not datetime_series.isna().all():
            return datetime_series
    except:
        pass
    
    # Return as is if no optimization possible
    return series


def get_type_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get type optimization recommendations for DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with recommendations
    """
    recommendations = []
    
    for col in df.columns:
        current_type = str(df[col].dtype)
        optimized = optimize_column_type(df[col])
        recommended_type = str(optimized.dtype)
        
        current_memory = df[col].memory_usage(deep=True)
        optimized_memory = optimized.memory_usage(deep=True)
        
        savings = current_memory - optimized_memory
        
        recommendations.append({
            'column': col,
            'current_type': current_type,
            'recommended_type': recommended_type,
            'current_memory_kb': current_memory / 1024,
            'optimized_memory_kb': optimized_memory / 1024,
            'savings_kb': savings / 1024,
            'savings_percent': (savings / current_memory * 100 
                               if current_memory > 0 else 0)
        })
    
    return pd.DataFrame(recommendations)


def convert_to_epidemiological_types(
    df: pd.DataFrame,
    column_types: Dict[str, str]
) -> pd.DataFrame:
    """
    Convert columns to specific epidemiological types.
    
    Args:
        df: Input DataFrame
        column_types: Dictionary of {column_name: type}
                     Types: 'binary', 'categorical', 'continuous', 'date'
        
    Returns:
        Converted DataFrame
    """
    df = df.copy()
    
    for col, col_type in column_types.items():
        if col in df.columns:
            if col_type == 'binary':
                df[col] = convert_to_binary(df[col])
            elif col_type == 'categorical':
                df[col] = convert_to_categorical(df[col])
            elif col_type == 'continuous':
                df[col] = convert_to_continuous(df[col])
            elif col_type == 'date':
                df[col] = convert_to_date(df[col])
    
    return df


def convert_to_binary(series: pd.Series) -> pd.Series:
    """Convert series to binary (0/1)."""
    # Handle various binary representations
    if series.dtype == 'bool':
        return series.astype(np.int8)
    
    # Check if already binary
    unique_vals = set(series.dropna().unique())
    if unique_vals.issubset({0, 1, 0.0, 1.0}):
        return series.astype(np.int8)
    
    # Try to convert from string representations
    str_lower = series.astype(str).str.lower()
    binary_map = {
        'true': 1, 'false': 0,
        'yes': 1, 'no': 0,
        'y': 1, 'n': 0,
        '1': 1, '0': 0,
        'positive': 1, 'negative': 0,
        'case': 1, 'control': 0
    }
    
    converted = str_lower.map(binary_map)
    if not converted.isna().all():
        return converted.astype(np.int8)
    
    # Fallback: convert to categorical and then to binary indicator
    return pd.get_dummies(series, drop_first=True).iloc[:, 0].astype(np.int8)


def convert_to_categorical(series: pd.Series, max_categories: int = 50) -> pd.Series:
    """Convert series to categorical type."""
    if series.dtype.name == 'category':
        return series
    
    n_unique = series.nunique()
    if n_unique > max_categories:
        warnings.warn(
            f"Column has {n_unique} unique values, "
            f"considering as continuous instead of categorical"
        )
        return series
    
    return series.astype('category')


def convert_to_continuous(series: pd.Series) -> pd.Series:
    """Convert series to continuous numeric type."""
    if pd.api.types.is_numeric_dtype(series):
        return optimize_numeric_type(series)
    
    # Try to convert to numeric
    try:
        numeric = pd.to_numeric(series, errors='coerce')
        if not numeric.isna().all():
            return optimize_numeric_type(numeric)
    except:
        pass
    
    return series


def convert_to_date(series: pd.Series) -> pd.Series:
    """Convert series to datetime type."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    
    try:
        return pd.to_datetime(series, errors='coerce')
    except:
        return series


def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect epidemiological column types automatically.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary of {column_name: detected_type}
    """
    type_map = {}
    
    for col in df.columns:
        series = df[col]
        
        # Check for date patterns
        if (series.dtype == 'object' and 
            series.dropna().astype(str).str.match(
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}').any()):
            type_map[col] = 'date'
        
        # Check for binary
        elif series.nunique() == 2:
            type_map[col] = 'binary'
        
        # Check for categorical (low cardinality)
        elif series.nunique() < 20 and series.nunique() < len(series) * 0.3:
            type_map[col] = 'categorical'
        
        # Check for numeric/continuous
        elif pd.api.types.is_numeric_dtype(series):
            type_map[col] = 'continuous'
        
        else:
            type_map[col] = 'unknown'
    
    return type_map
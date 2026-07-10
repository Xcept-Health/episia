"""
This module provides functions for reading and writing epidemiological
data in various formats with automatic format detection and validation.
"""

import pandas as pd
from typing import Union, Dict, List
from pathlib import Path


from ..core.exceptions import FileError 
from .dataset import Dataset


def read_csv(
    path: Union[str, Path],
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Read CSV file into Dataset.
    
    Args:
        path: Path to CSV file
        low_memory: Optimize memory usage
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        Dataset object
    """
    try:
        df = pd.read_csv(path, **kwargs)
        return Dataset(df, low_memory=low_memory)
    except Exception as e:
        raise FileError(f"Failed to read CSV file {path}: {e}")


def read_excel(
    path: Union[str, Path],
    sheet_name: Union[str, int, List, None] = 0,
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Read Excel file into Dataset.
    
    Args:
        path: Path to Excel file
        sheet_name: Sheet to read
        low_memory: Optimize memory usage
        **kwargs: Additional arguments for pd.read_excel
        
    Returns:
        Dataset object
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
        return Dataset(df, low_memory=low_memory)
    except Exception as e:
        raise FileError(f"Failed to read Excel file {path}: {e}")


def read_parquet(
    path: Union[str, Path],
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Read Parquet file into Dataset.
    
    Args:
        path: Path to Parquet file
        low_memory: Optimize memory usage
        **kwargs: Additional arguments for pd.read_parquet
        
    Returns:
        Dataset object
    """
    try:
        df = pd.read_parquet(path, **kwargs)
        return Dataset(df, low_memory=low_memory)
    except Exception as e:
        raise FileError(f"Failed to read Parquet file {path}: {e}")


def from_pandas(
    df: pd.DataFrame,
    low_memory: bool = True
) -> Dataset:
    """
    Create Dataset from pandas DataFrame.
    
    Args:
        df: pandas DataFrame
        low_memory: Optimize memory usage
        
    Returns:
        Dataset object
    """
    return Dataset(df, low_memory=low_memory)


def from_dict(
    data: Dict,
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Create Dataset from dictionary.
    
    Args:
        data: Dictionary of data
        low_memory: Optimize memory usage
        **kwargs: Additional arguments for pd.DataFrame
        
    Returns:
        Dataset object
    """
    df = pd.DataFrame(data, **kwargs)
    return Dataset(df, low_memory=low_memory)


def from_records(
    records: List[Dict],
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Create Dataset from list of records.
    
    Args:
        records: List of dictionaries
        low_memory: Optimize memory usage
        **kwargs: Additional arguments for pd.DataFrame.from_records
        
    Returns:
        Dataset object
    """
    df = pd.DataFrame.from_records(records, **kwargs)
    return Dataset(df, low_memory=low_memory)


def read_surveillance_format(
    path: Union[str, Path],
    format_type: str = 'auto',
    low_memory: bool = True,
    **kwargs
) -> Dataset:
    """
    Read surveillance data in standard formats.

    .. warning::
        Parsers for named surveillance standards ('sidesp', 'who', 'ecdc')
        are not yet implemented. This function currently only supports
        generic tabular files (CSV/Excel/Parquet) via ``format_type='auto'``.
        Passing 'sidesp', 'who', or 'ecdc' raises ``NotImplementedError``
        rather than silently misreading the file.

    Args:
        path: Path to surveillance data file
        format_type: Format type ('sidesp', 'who', 'ecdc', 'auto')
        low_memory: Optimize memory usage
        **kwargs: Additional arguments passed to the underlying reader

    Returns:
        Dataset object

    Raises:
        NotImplementedError: If format_type is a named surveillance
            standard ('sidesp', 'who', 'ecdc'), since no parser for it
            exists yet.
        FileError: If the file cannot be read.
    """
    if format_type == 'auto':
        detected = detect_format(path)
        if detected == 'csv':
            return read_csv(path, low_memory=low_memory, **kwargs)
        if detected == 'excel':
            return read_excel(path, low_memory=low_memory, **kwargs)
        if detected == 'parquet':
            return read_parquet(path, low_memory=low_memory, **kwargs)
        raise FileError(
            f"Could not auto-detect a supported format for {path} "
            f"(detected: '{detected}'). Use read_csv/read_excel/read_parquet directly."
        )

    if format_type in ('sidesp', 'who', 'ecdc'):
        raise NotImplementedError(
            f"format_type='{format_type}' is not implemented yet. "
            "Only format_type='auto' (generic CSV/Excel/Parquet) is currently supported. "
            "Contributions implementing SIDESP/WHO/ECDC-specific parsing are welcome."
        )

    raise ValueError(
        f"Unknown format_type: '{format_type}'. "
        "Expected one of: 'auto', 'sidesp', 'who', 'ecdc'."
    )


def detect_format(path: Union[str, Path]) -> str:
    """
    Detect file format from extension or content.
    
    Args:
        path: Path to file
        
    Returns:
        Detected format string
    """
    path = Path(path)
    suffix = path.suffix.lower()
    
    format_map = {
        '.csv': 'csv',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.parquet': 'parquet',
        '.feather': 'feather',
        '.json': 'json',
        '.txt': 'text'
    }
    
    return format_map.get(suffix, 'unknown')


def export_dataset(
    dataset: Dataset,
    path: Union[str, Path],
    format: str = 'auto',
    **kwargs
) -> None:
    """
    Export Dataset to file.
    
    Args:
        dataset: Dataset to export
        path: Output path
        format: Output format ('csv', 'excel', 'parquet', 'auto')
        **kwargs: Additional arguments for writer
    """
    path = Path(path)
    
    if format == 'auto':
        format = detect_format(path)
    
    try:
        if format == 'csv':
            dataset.df.to_csv(path, **kwargs)
        elif format in ['excel', 'xlsx', 'xls']:
            dataset.df.to_excel(path, **kwargs)
        elif format == 'parquet':
            dataset.df.to_parquet(path, **kwargs)
        elif format == 'json':
            dataset.df.to_json(path, **kwargs)
        else:
            raise FileError(f"Unsupported export format: {format}")
    except Exception as e:
        raise FileError(f"Failed to export dataset: {e}")
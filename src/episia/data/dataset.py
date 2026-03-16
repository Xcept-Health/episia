"""
This module provides the Dataset class, a pandas DataFrame wrapper
optimized for epidemiological analysis with additional functionality
for cleaning, transforming, and analyzing public health data.
"""

import pandas as pd
from typing import Union, List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from ..core.validator import validate_dataframe, validate_binary_variable
from ..core.exceptions import DataError, ValidationError
from ..core.utilities import timer


class Dataset:
    """
    Dataset class for epidemiological data.
    
    A pandas DataFrame wrapper with epidemiological-specific methods
    and optimizations for memory and performance.
    
    Attributes:
        df: Underlying pandas DataFrame
        metadata: Dictionary with dataset metadata
        history: List of transformations applied
        optimized: Whether data types have been optimized
    """
    
    def __init__(
        self,
        data: Union[pd.DataFrame, Dict, str, Path],
        low_memory: bool = True,
        **kwargs
    ):
        """
        Initialize Dataset from various data sources.
        
        Args:
            data: DataFrame, dictionary, or file path
            low_memory: Optimize memory usage if True
            **kwargs: Additional arguments for pd.read_csv if data is path
            
        Raises:
            DataError: If data cannot be loaded
        """
        self.history: List[Dict] = []
        self.metadata: Dict[str, Any] = {
            'created': datetime.now(),
            'source': str(data) if isinstance(data, (str, Path)) else 'object',
            'optimized': False
        }
        
        # Load data
        self.df = self._load_data(data, **kwargs)
        
        # Validate
        try:
            self.df = validate_dataframe(self.df, min_rows=1)
        except ValidationError as e:
            raise DataError(f"Invalid dataset: {e}")
        
        # Optimize memory if requested
        if low_memory:
            self.optimize_types()
        
        # Record initialization
        self.history.append({
            'timestamp': datetime.now(),
            'operation': 'init',
            'details': f"Loaded {len(self.df)} rows, {len(self.df.columns)} columns"
        })
    
    def _load_data(
        self, 
        data: Union[pd.DataFrame, Dict, str, Path],
        **kwargs
    ) -> pd.DataFrame:
        """Load data from various sources."""
        if isinstance(data, pd.DataFrame):
            return data.copy()
        
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        
        elif isinstance(data, (str, Path)):
            path = Path(data)
            if not path.exists():
                raise DataError(f"File not found: {path}")
            
            # Determine file type
            suffix = path.suffix.lower()
            
            if suffix == '.csv':
                return pd.read_csv(path, **kwargs)
            elif suffix in ['.xlsx', '.xls']:
                return pd.read_excel(path, **kwargs)
            elif suffix == '.parquet':
                return pd.read_parquet(path, **kwargs)
            elif suffix == '.feather':
                return pd.read_feather(path, **kwargs)
            elif suffix == '.json':
                return pd.read_json(path, **kwargs)
            else:
                raise DataError(f"Unsupported file format: {suffix}")
        
        else:
            raise DataError(f"Unsupported data type: {type(data)}")
    
    def optimize_types(self) -> 'Dataset':
        """
        Optimize DataFrame column types to reduce memory usage.
        
        Returns:
            self for method chaining
        """
        from .types import optimize_dataframe_types
        
        original_memory = self.df.memory_usage(deep=True).sum()
        self.df = optimize_dataframe_types(self.df)
        optimized_memory = self.df.memory_usage(deep=True).sum()
        
        reduction = ((original_memory - optimized_memory) / original_memory * 100
                    if original_memory > 0 else 0)
        
        self.metadata['optimized'] = True
        self.metadata['memory_reduction_pct'] = reduction
        
        self.history.append({
            'timestamp': datetime.now(),
            'operation': 'optimize_types',
            'details': f"Memory reduced by {reduction:.1f}%"
        })
        
        return self
    
    @timer
    def clean(
        self,
        drop_na: Union[bool, str, List[str]] = 'any',
        drop_duplicates: bool = True,
        inplace: bool = False
    ) -> 'Dataset':
        """
        Clean the dataset by removing missing values and duplicates.
        
        Args:
            drop_na: How to handle missing values:
                    True/'any': Drop rows with any NaN
                    'all': Drop rows with all NaN
                    List: Drop rows with NaN in specific columns
            drop_duplicates: Remove duplicate rows
            inplace: Modify in place or return new Dataset
            
        Returns:
            Cleaned Dataset
        """
        dataset = self if inplace else self.copy()
        
        # Remove missing values
        if drop_na:
            if isinstance(drop_na, list):
                dataset.df = dataset.df.dropna(subset=drop_na)
            elif drop_na == 'all':
                dataset.df = dataset.df.dropna(how='all')
            else:
                dataset.df = dataset.df.dropna()
        
        # Remove duplicates
        if drop_duplicates:
            before = len(dataset.df)
            dataset.df = dataset.df.drop_duplicates()
            duplicates_removed = before - len(dataset.df)
        
        dataset.history.append({
            'timestamp': datetime.now(),
            'operation': 'clean',
            'details': f"Removed NaN and duplicates, {len(dataset.df)} rows remaining"
        })
        
        return dataset
    
    def filter(
        self,
        condition: Union[str, Dict, pd.Series],
        inplace: bool = False
    ) -> 'Dataset':
        """
        Filter dataset based on condition.
        
        Args:
            condition: Filter condition as:
                      - Query string
                      - Dictionary of {column: value}
                      - Boolean Series
            inplace: Modify in place or return new Dataset
            
        Returns:
            Filtered Dataset
        """
        dataset = self if inplace else self.copy()
        
        if isinstance(condition, str):
            dataset.df = dataset.df.query(condition)
        elif isinstance(condition, dict):
            for col, val in condition.items():
                if col in dataset.df.columns:
                    dataset.df = dataset.df[dataset.df[col] == val]
        elif isinstance(condition, pd.Series):
            dataset.df = dataset.df[condition]
        else:
            raise DataError("Condition must be string, dict, or Series")
        
        dataset.history.append({
            'timestamp': datetime.now(),
            'operation': 'filter',
            'details': f"Filtered to {len(dataset.df)} rows"
        })
        
        return dataset
    
    def aggregate_by_date(
        self,
        date_column: str = 'date',
        freq: str = 'W',
        agg_func: Union[str, Dict] = 'sum',
        inplace: bool = False
    ) -> 'Dataset':
        """
        Aggregate data by date frequency.
        
        Args:
            date_column: Name of date column
            freq: Frequency string ('D', 'W', 'M', 'Y')
            agg_func: Aggregation function or dict of {column: function}
            inplace: Modify in place or return new Dataset
            
        Returns:
            Aggregated Dataset
        """
        dataset = self if inplace else self.copy()
        
        if date_column not in dataset.df.columns:
            raise DataError(f"Date column '{date_column}' not found")
        
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(dataset.df[date_column]):
            dataset.df[date_column] = pd.to_datetime(dataset.df[date_column])
        
        # Set date as index and resample
        dataset.df = dataset.df.set_index(date_column)
        dataset.df = dataset.df.resample(freq).agg(agg_func)
        dataset.df = dataset.df.reset_index()
        
        dataset.history.append({
            'timestamp': datetime.now(),
            'operation': 'aggregate_by_date',
            'details': f"Aggregated by {freq} frequency"
        })
        
        return dataset
    
    def create_2x2_table(
        self,
        exposure_col: str,
        outcome_col: str,
        strata_col: Optional[str] = None
    ) -> Dict:
        """
        Create 2x2 contingency table from dataset columns.
        
        Args:
            exposure_col: Exposure variable column
            outcome_col: Outcome variable column
            strata_col: Stratification variable (optional)
            
        Returns:
            Dictionary with table(s) and statistics
        """
        from ..stats.contingency import Table2x2, from_dataframe
        
        # Validate binary columns
        for col in [exposure_col, outcome_col]:
            try:
                self.df[col] = validate_binary_variable(self.df[col], col)
            except ValidationError:
                # Convert to binary if not already
                self.df[col] = self.df[col].astype(bool).astype(int)
        
        if strata_col:
            # Create stratified tables
            tables = {}
            for stratum, group in self.df.groupby(strata_col):
                table = from_dataframe(group, exposure_col, outcome_col)
                tables[stratum] = table
            return {'strata': tables, 'type': 'stratified'}
        else:
            # Create single table
            table = from_dataframe(self.df, exposure_col, outcome_col)
            return {'table': table, 'type': 'single'}
    
    def calculate_incidence(
        self,
        cases_col: str,
        population_col: Optional[str] = None,
        population_value: Optional[float] = None,
        time_period: float = 1.0
    ) -> pd.Series:
        """
        Calculate incidence rates.
        
        Args:
            cases_col: Column with case counts
            population_col: Column with population at risk
            population_value: Constant population value if no column
            time_period: Time period for rate
            
        Returns:
            Series with incidence rates
        """
        from ..stats.time_series import calculate_incidence
        
        if population_col:
            population = self.df[population_col]
        elif population_value:
            population = population_value
        else:
            raise DataError("Must provide population_col or population_value")
        
        cases = self.df[cases_col]
        incidence = calculate_incidence(cases, population, time_period)
        
        return incidence
    
    def describe_epidemiological(self) -> pd.DataFrame:
        """
        Generate epidemiological description of dataset.
        
        Returns:
            DataFrame with epidemiological summary
        """
        summary = []
        
        for col in self.df.columns:
            col_data = self.df[col]
            col_type = str(col_data.dtype)
            
            # Basic statistics
            stats = {
                'column': col,
                'type': col_type,
                'non_null': col_data.count(),
                'null': col_data.isnull().sum(),
                'unique': col_data.nunique()
            }
            
            # Numerical columns
            if pd.api.types.is_numeric_dtype(col_data):
                stats.update({
                    'mean': col_data.mean(),
                    'std': col_data.std(),
                    'min': col_data.min(),
                    'max': col_data.max(),
                    'median': col_data.median()
                })
            
            # Categorical columns
            elif pd.api.types.is_categorical_dtype(col_data) or col_data.nunique() < 20:
                stats['top_categories'] = col_data.value_counts().head(3).to_dict()
            
            # Date columns
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                stats.update({
                    'start': col_data.min(),
                    'end': col_data.max(),
                    'range_days': (col_data.max() - col_data.min()).days
                })
            
            summary.append(stats)
        
        return pd.DataFrame(summary)
    
    def copy(self) -> 'Dataset':
        """Create a copy of the Dataset."""
        import copy
        
        new_dataset = Dataset.__new__(Dataset)
        new_dataset.df = self.df.copy()
        new_dataset.history = copy.deepcopy(self.history)
        new_dataset.metadata = copy.deepcopy(self.metadata)
        
        return new_dataset
    
    def to_csv(self, path: Union[str, Path], **kwargs) -> None:
        """Save dataset to CSV."""
        self.df.to_csv(path, **kwargs)
    
    def to_parquet(self, path: Union[str, Path], **kwargs) -> None:
        """Save dataset to Parquet."""
        self.df.to_parquet(path, **kwargs)
    
    def get_history(self) -> pd.DataFrame:
        """Get transformation history as DataFrame."""
        return pd.DataFrame(self.history)
    
    def __len__(self) -> int:
        return len(self.df)
    
    def __repr__(self) -> str:
        return f"Dataset(rows={len(self.df)}, cols={len(self.df.columns)}, history={len(self.history)})"
    
    def __getitem__(self, key):
        """Allow dictionary-like access to columns."""
        if isinstance(key, str):
            return self.df[key]
        elif isinstance(key, list):
            return self.df[key]
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
    
    def __setitem__(self, key, value):
        """Allow dictionary-like assignment to columns."""
        self.df[key] = value
        
        self.history.append({
            'timestamp': datetime.now(),
            'operation': 'set_column',
            'details': f"Set column '{key}'"
        })
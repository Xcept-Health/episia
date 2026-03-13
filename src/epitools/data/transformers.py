"""
This module provides transformer classes and functions for cleaning,
normalizing, and preparing epidemiological data for analysis.
"""

import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any, Optional, Callable
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from ..core.exceptions import DataError


class EpidemiologicalTransformer(BaseEstimator, TransformerMixin):
    """
    Base transformer for epidemiological data.
    
    Provides common functionality for data transformation
    with fit/transform interface compatible with scikit-learn.
    """
    
    def __init__(self):
        self.is_fitted = False
    
    def fit(self, X: pd.DataFrame, y=None):
        """Fit transformer to data."""
        self.is_fitted = True
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform data."""
        if not self.is_fitted:
            raise DataError("Transformer must be fitted before transforming")
        return X
    
    def fit_transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        """Fit and transform data."""
        return self.fit(X).transform(X)


class DateTransformer(EpidemiologicalTransformer):
    """
    Transformer for date column processing.
    """
    
    def __init__(
        self,
        date_columns: Union[str, List[str]],
        extract_features: bool = True
    ):
        super().__init__()
        self.date_columns = ([date_columns] if isinstance(date_columns, str) 
                            else date_columns)
        self.extract_features = extract_features
        self.extracted_features_ = []
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform date columns."""
        X = X.copy()
        
        for col in self.date_columns:
            if col in X.columns:
                # Convert to datetime
                X[col] = pd.to_datetime(X[col], errors='coerce')
                
                if self.extract_features:
                    # Extract temporal features
                    X[f"{col}_year"] = X[col].dt.year
                    X[f"{col}_month"] = X[col].dt.month
                    X[f"{col}_day"] = X[col].dt.day
                    X[f"{col}_week"] = X[col].dt.isocalendar().week
                    X[f"{col}_dayofweek"] = X[col].dt.dayofweek
                    X[f"{col}_quarter"] = X[col].dt.quarter
                    
                    self.extracted_features_.extend([
                        f"{col}_year", f"{col}_month", f"{col}_day",
                        f"{col}_week", f"{col}_dayofweek", f"{col}_quarter"
                    ])
        
        return X


class CategoricalTransformer(EpidemiologicalTransformer):
    """
    Transformer for categorical variable encoding.
    """
    
    def __init__(
        self,
        categorical_columns: List[str],
        encoding: str = 'onehot',
        max_categories: int = 20,
        handle_unknown: str = 'ignore'
    ):
        super().__init__()
        self.categorical_columns = categorical_columns
        self.encoding = encoding
        self.max_categories = max_categories
        self.handle_unknown = handle_unknown
        self.category_mappings_ = {}
    
    def fit(self, X: pd.DataFrame, y=None):
        """Learn categories from data."""
        for col in self.categorical_columns:
            if col in X.columns:
                unique_cats = X[col].dropna().unique()
                if len(unique_cats) <= self.max_categories:
                    self.category_mappings_[col] = list(unique_cats)
        
        self.is_fitted = True
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical variables."""
        X = X.copy()
        
        for col, categories in self.category_mappings_.items():
            if col in X.columns:
                if self.encoding == 'onehot':
                    # One-hot encoding
                    for cat in categories:
                        X[f"{col}_{cat}"] = (X[col] == cat).astype(int)
                    X = X.drop(columns=[col])
                
                elif self.encoding == 'label':
                    # Label encoding
                    cat_map = {cat: i for i, cat in enumerate(categories)}
                    X[col] = X[col].map(cat_map)
                    X[col] = X[col].fillna(-1).astype(int)
        
        return X


class OutlierTransformer(EpidemiologicalTransformer):
    """
    Transformer for outlier detection and handling.
    """
    
    def __init__(
        self,
        numeric_columns: List[str],
        method: str = 'iqr',
        threshold: float = 1.5,
        action: str = 'clip'
    ):
        super().__init__()
        self.numeric_columns = numeric_columns
        self.method = method
        self.threshold = threshold
        self.action = action
        self.bounds_ = {}
    
    def fit(self, X: pd.DataFrame, y=None):
        """Calculate outlier bounds."""
        for col in self.numeric_columns:
            if col in X.columns and pd.api.types.is_numeric_dtype(X[col]):
                data = X[col].dropna()
                
                if self.method == 'iqr':
                    q1 = data.quantile(0.25)
                    q3 = data.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - self.threshold * iqr
                    upper = q3 + self.threshold * iqr
                
                elif self.method == 'zscore':
                    mean = data.mean()
                    std = data.std()
                    lower = mean - self.threshold * std
                    upper = mean + self.threshold * std
                
                else:
                    raise DataError(f"Unknown outlier method: {self.method}")
                
                self.bounds_[col] = {'lower': lower, 'upper': upper}
        
        self.is_fitted = True
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Handle outliers."""
        X = X.copy()
        
        for col, bounds in self.bounds_.items():
            if col in X.columns:
                if self.action == 'clip':
                    X[col] = X[col].clip(bounds['lower'], bounds['upper'])
                elif self.action == 'remove':
                    mask = (X[col] >= bounds['lower']) & (X[col] <= bounds['upper'])
                    X = X[mask]
                elif self.action == 'nullify':
                    mask = (X[col] < bounds['lower']) | (X[col] > bounds['upper'])
                    X.loc[mask, col] = np.nan
        
        return X


class FeatureEngineer(EpidemiologicalTransformer):
    """
    Transformer for epidemiological feature engineering.
    """
    
    def __init__(self):
        super().__init__()
        self.created_features_ = []
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Create epidemiological features."""
        X = X.copy()
        
        # Age group categorization
        if 'age' in X.columns:
            bins = [0, 18, 30, 40, 50, 60, 70, 80, 90, 100, 120]
            labels = ['0-17', '18-29', '30-39', '40-49', '50-59', 
                     '60-69', '70-79', '80-89', '90-99', '100+']
            X['age_group'] = pd.cut(X['age'], bins=bins, labels=labels, right=False)
            self.created_features_.append('age_group')
        
        # BMI calculation if height and weight available
        if all(col in X.columns for col in ['height_cm', 'weight_kg']):
            X['bmi'] = X['weight_kg'] / ((X['height_cm'] / 100) ** 2)
            X['bmi_category'] = pd.cut(X['bmi'], 
                                      bins=[0, 18.5, 25, 30, 35, 40, 100],
                                      labels=['Underweight', 'Normal', 'Overweight',
                                              'Obese I', 'Obese II', 'Obese III'])
            self.created_features_.extend(['bmi', 'bmi_category'])
        
        # Create interaction terms for common epidemiological variables
        interaction_pairs = []
        if 'smoking' in X.columns and 'alcohol' in X.columns:
            interaction_pairs.append(('smoking', 'alcohol'))
        if 'hypertension' in X.columns and 'diabetes' in X.columns:
            interaction_pairs.append(('hypertension', 'diabetes'))
        
        for var1, var2 in interaction_pairs:
            if var1 in X.columns and var2 in X.columns:
                interaction_name = f"{var1}_x_{var2}"
                X[interaction_name] = X[var1] * X[var2]
                self.created_features_.append(interaction_name)
        
        return X


def create_pipeline(transformers: List[EpidemiologicalTransformer]) -> Callable:
    """
    Create a transformation pipeline from list of transformers.
    
    Args:
        transformers: List of transformer instances
        
    Returns:
        Pipeline function
    """
    def pipeline(X: pd.DataFrame) -> pd.DataFrame:
        for transformer in transformers:
            X = transformer.fit_transform(X)
        return X
    
    return pipeline


def normalize_data(
    df: pd.DataFrame,
    columns: List[str],
    method: str = 'standard',
    **kwargs
) -> pd.DataFrame:
    """
    Normalize numerical columns.
    
    Args:
        df: Input DataFrame
        columns: Columns to normalize
        method: Normalization method ('standard', 'minmax', 'robust')
        **kwargs: Additional arguments for scaler
        
    Returns:
        Normalized DataFrame
    """
    df = df.copy()
    
    for col in columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            data = df[col].values.reshape(-1, 1)
            
            if method == 'standard':
                scaler = StandardScaler(**kwargs)
            elif method == 'minmax':
                scaler = MinMaxScaler(**kwargs)
            elif method == 'robust':
                from sklearn.preprocessing import RobustScaler
                scaler = RobustScaler(**kwargs)
            else:
                raise DataError(f"Unknown normalization method: {method}")
            
            df[col] = scaler.fit_transform(data).flatten()
    
    return df
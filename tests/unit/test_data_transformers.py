"""
tests/test_data_transformers.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import pandas as pd
import numpy as np
from episia.data.transformers import (
    DateTransformer, CategoricalTransformer,
    OutlierTransformer, FeatureEngineer, create_pipeline,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'date':     ['2024-01-01','2024-01-08','2024-01-15','2024-01-22'],
        'region':   ['A','B','A','C'],
        'disease':  ['malaria','measles','malaria','cholera'],
        'cases':    [10, 20, 15, 5],
        'deaths':   [1, 2, 1, 0],
        'value':    [1.0, 2.0, 1.5, 100.0],  # 100.0 is an outlier
    })


class TestDateTransformer:

    def test_returns_dataframe(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert isinstance(result, pd.DataFrame)

    def test_adds_year_column(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert 'date_year' in result.columns

    def test_adds_month_column(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert 'date_month' in result.columns

    def test_adds_week_column(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert 'date_week' in result.columns

    def test_adds_day_column(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert 'date_day' in result.columns

    def test_year_values_correct(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert (result['date_year'] == 2024).all()

    def test_month_values_correct(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert (result['date_month'] == 1).all()

    def test_row_count_preserved(self, sample_df):
        dt = DateTransformer(date_columns='date')
        result = dt.fit_transform(sample_df.copy())
        assert len(result) == len(sample_df)

    def test_no_features_extract(self, sample_df):
        dt = DateTransformer(date_columns='date', extract_features=False)
        result = dt.fit_transform(sample_df.copy())
        assert 'date_year' not in result.columns

    def test_fit_then_transform(self, sample_df):
        dt = DateTransformer(date_columns='date')
        dt.fit(sample_df.copy())
        result = dt.transform(sample_df.copy())
        assert 'date_year' in result.columns


class TestCategoricalTransformer:

    def test_returns_dataframe(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region'])
        result = ct.fit_transform(sample_df.copy())
        assert isinstance(result, pd.DataFrame)

    def test_onehot_creates_binary_columns(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region'], encoding='onehot')
        result = ct.fit_transform(sample_df.copy())
        onehot_cols = [c for c in result.columns if c.startswith('region_')]
        assert len(onehot_cols) > 0

    def test_onehot_binary_values(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region'], encoding='onehot')
        result = ct.fit_transform(sample_df.copy())
        onehot_cols = [c for c in result.columns if c.startswith('region_')]
        for col in onehot_cols:
            assert set(result[col].unique()).issubset({0, 1})

    def test_original_col_removed_onehot(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region'], encoding='onehot')
        result = ct.fit_transform(sample_df.copy())
        assert 'region' not in result.columns

    def test_row_count_preserved(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region'])
        result = ct.fit_transform(sample_df.copy())
        assert len(result) == len(sample_df)

    def test_multiple_columns(self, sample_df):
        ct = CategoricalTransformer(categorical_columns=['region', 'disease'])
        result = ct.fit_transform(sample_df.copy())
        assert 'region' not in result.columns
        assert 'disease' not in result.columns


class TestOutlierTransformer:

    def test_returns_dataframe(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'])
        result = ot.fit_transform(sample_df.copy())
        assert isinstance(result, pd.DataFrame)

    def test_clip_action_reduces_outlier(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'], method='iqr', action='clip')
        result = ot.fit_transform(sample_df.copy())
        assert result['value'].max() < 100.0

    def test_row_count_preserved(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'], action='clip')
        result = ot.fit_transform(sample_df.copy())
        assert len(result) == len(sample_df)

    def test_non_outlier_values_unchanged(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'], action='clip')
        result = ot.fit_transform(sample_df.copy())
        assert result['value'].iloc[0] == sample_df['value'].iloc[0]

    def test_cases_column_not_affected(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'])
        result = ot.fit_transform(sample_df.copy())
        assert result['cases'].tolist() == sample_df['cases'].tolist()

    def test_fit_then_transform(self, sample_df):
        ot = OutlierTransformer(numeric_columns=['value'])
        ot.fit(sample_df.copy())
        result = ot.transform(sample_df.copy())
        assert isinstance(result, pd.DataFrame)


class TestCreatePipeline:

    def test_pipeline_returns_callable(self, sample_df):
        transformers = [
            DateTransformer(date_columns='date'),
            CategoricalTransformer(categorical_columns=['region']),
        ]
        pipeline = create_pipeline(transformers)
        assert callable(pipeline)

    def test_pipeline_applies_transformers(self, sample_df):
        transformers = [
            DateTransformer(date_columns='date'),
        ]
        pipeline = create_pipeline(transformers)
        result = pipeline(sample_df.copy())
        assert 'date_year' in result.columns
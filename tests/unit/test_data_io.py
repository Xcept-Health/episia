"""
tests/test_data_io.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from episia.data.io import read_csv, from_pandas, from_dict, export_dataset, detect_format
from episia.data.dataset import Dataset


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'date':     ['2024-01-01','2024-01-08','2024-01-15'],
        'cases':    [10, 25, 18],
        'deaths':   [1, 2, 1],
        'district': ['Ouagadougou','Bobo','Koudougou'],
    })

@pytest.fixture
def csv_file(sample_df):
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False, newline='') as f:
        sample_df.to_csv(f, index=False)
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def excel_file(sample_df):
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    sample_df.to_excel(path, index=False)
    yield path
    os.unlink(path)


class TestReadCsv:

    def test_returns_dataset(self, csv_file):
        ds = read_csv(csv_file)
        assert isinstance(ds, Dataset)

    def test_correct_row_count(self, csv_file):
        ds = read_csv(csv_file)
        assert len(ds.df) == 3

    def test_correct_col_count(self, csv_file):
        ds = read_csv(csv_file)
        assert len(ds.df.columns) == 4

    def test_columns_preserved(self, csv_file):
        ds = read_csv(csv_file)
        for col in ('date', 'cases', 'deaths', 'district'):
            assert col in ds.df.columns

    def test_pathlib_path(self, csv_file):
        from pathlib import Path
        ds = read_csv(Path(csv_file))
        assert isinstance(ds, Dataset)

    def test_nonexistent_file_raises(self):
        with pytest.raises(Exception):
            read_csv('/tmp/nonexistent_episia_test.csv')


class TestFromPandas:

    def test_returns_dataset(self, sample_df):
        ds = from_pandas(sample_df)
        assert isinstance(ds, Dataset)

    def test_row_count_preserved(self, sample_df):
        ds = from_pandas(sample_df)
        assert len(ds.df) == 3

    def test_columns_preserved(self, sample_df):
        ds = from_pandas(sample_df)
        for col in sample_df.columns:
            assert col in ds.df.columns

    def test_data_preserved(self, sample_df):
        ds = from_pandas(sample_df)
        assert ds.df['cases'].sum() == sample_df['cases'].sum()

    def test_empty_dataframe_raises(self):
        from episia.core.exceptions import ValidationError
        df = pd.DataFrame(columns=['a','b'])
        with pytest.raises((ValidationError, Exception)):
            from_pandas(df)


class TestFromDict:

    def test_returns_dataset(self):
        ds = from_dict({'cases':[1,2,3], 'date':['2024-01-01','2024-01-08','2024-01-15']})
        assert isinstance(ds, Dataset)

    def test_row_count(self):
        ds = from_dict({'a':[1,2,3,4], 'b':[5,6,7,8]})
        assert len(ds.df) == 4

    def test_columns(self):
        ds = from_dict({'x':[1,2], 'y':[3,4]})
        assert 'x' in ds.df.columns
        assert 'y' in ds.df.columns


class TestExportDataset:

    def test_export_csv(self, sample_df):
        ds = from_pandas(sample_df)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = f.name
        try:
            export_dataset(ds, path, format='csv')
            assert os.path.exists(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_export_csv_readable(self, sample_df):
        ds = from_pandas(sample_df)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = f.name
        try:
            export_dataset(ds, path, format='csv')
            df2 = pd.read_csv(path)
            assert len(df2) == len(sample_df)
        finally:
            os.unlink(path)

    def test_export_auto_format_csv(self, sample_df):
        ds = from_pandas(sample_df)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = f.name
        try:
            export_dataset(ds, path, format='auto')
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)


class TestDetectFormat:

    def test_csv_extension(self):
        fmt = detect_format('/some/path/data.csv')
        assert fmt == 'csv'

    def test_excel_extension(self):
        fmt = detect_format('/some/path/data.xlsx')
        assert fmt in ('excel', 'xlsx')

    def test_parquet_extension(self):
        fmt = detect_format('/some/path/data.parquet')
        assert fmt == 'parquet'
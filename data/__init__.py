"""
Data module for EpiTools - Epidemiological data management.

This module provides tools for loading, cleaning, transforming,
and managing epidemiological data with specialized functionality
for public health analysis.
"""

from .dataset import Dataset
from .io import (
    read_csv,
    read_excel,
    read_parquet,
    read_surveillance_format,
    from_pandas,
    from_dict,
    from_records,
    detect_format,
    export_dataset
)
from .transformers import (
    EpidemiologicalTransformer,
    DateTransformer,
    CategoricalTransformer,
    OutlierTransformer,
    FeatureEngineer,
    create_pipeline,
    normalize_data
)
from .types import (
    optimize_dataframe_types,
    optimize_column_type,
    get_type_recommendations,
    convert_to_epidemiological_types,
    detect_column_types,
    convert_to_binary,
    convert_to_categorical,
    convert_to_continuous,
    convert_to_date
)
from .surveillance import (
    read_format,
    read_sidesp,
    read_who_goarn,
    read_ecdc,
    validate_surveillance_format,
    detect_surveillance_format,
    convert_to_format,
    convert_to_sidesp,
    convert_to_who,
    convert_to_ecdc,
    get_disease_codes,
    map_disease_codes,
    SIDEP_COLUMNS,
    WHO_GOARN_COLUMNS,
    ECDC_COLUMNS
)

__all__ = [
    # Main Dataset class
    'Dataset',
    
    # IO functions
    'read_csv',
    'read_excel',
    'read_parquet',
    'read_surveillance_format',
    'from_pandas',
    'from_dict',
    'from_records',
    'detect_format',
    'export_dataset',
    
    # Transformers
    'EpidemiologicalTransformer',
    'DateTransformer',
    'CategoricalTransformer',
    'OutlierTransformer',
    'FeatureEngineer',
    'create_pipeline',
    'normalize_data',
    
    # Type optimization
    'optimize_dataframe_types',
    'optimize_column_type',
    'get_type_recommendations',
    'convert_to_epidemiological_types',
    'detect_column_types',
    'convert_to_binary',
    'convert_to_categorical',
    'convert_to_continuous',
    'convert_to_date',
    
    # Surveillance formats
    'read_format',
    'read_sidesp',
    'read_who_goarn',
    'read_ecdc',
    'validate_surveillance_format',
    'detect_surveillance_format',
    'convert_to_format',
    'convert_to_sidesp',
    'convert_to_who',
    'convert_to_ecdc',
    'get_disease_codes',
    'map_disease_codes',
    'SIDEP_COLUMNS',
    'WHO_GOARN_COLUMNS',
    'ECDC_COLUMNS'
]
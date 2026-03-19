types Module
============

Data type optimization for epidemiological analysis.

This module provides functions for optimizing data types to reduce
memory usage while maintaining data integrity for epidemiological analysis.

Functions
---------

.. autofunction:: episia.data.types.optimize_dataframe_types
.. autofunction:: episia.data.types.optimize_column_type
.. autofunction:: episia.data.types.optimize_numeric_type
.. autofunction:: episia.data.types.optimize_datetime_type
.. autofunction:: episia.data.types.optimize_object_type
.. autofunction:: episia.data.types.get_type_recommendations
.. autofunction:: episia.data.types.convert_to_epidemiological_types
.. autofunction:: episia.data.types.convert_to_binary
.. autofunction:: episia.data.types.convert_to_categorical
.. autofunction:: episia.data.types.convert_to_continuous
.. autofunction:: episia.data.types.convert_to_date
.. autofunction:: episia.data.types.detect_column_types

Examples
--------

Optimize entire DataFrame::

    from episia.data.types import optimize_dataframe_types
    import pandas as pd

    # Create DataFrame with inefficient types
    df = pd.DataFrame({
        'age': [25, 30, 35, 40],
        'cases': [100, 150, 200, 250],
        'district': ['A', 'B', 'A', 'C']
    })

    # Optimize types
    df_opt = optimize_dataframe_types(df)
    # Memory usage is automatically reduced

Get type recommendations::

    from episia.data.types import get_type_recommendations

    recommendations = get_type_recommendations(df)
    print(recommendations)
    # Shows current vs recommended types and memory savings

Convert to specific epidemiological types::

    from episia.data.types import convert_to_epidemiological_types

    type_spec = {
        'district': 'categorical',
        'case': 'binary',
        'age': 'continuous',
        'report_date': 'date'
    }

    df_converted = convert_to_epidemiological_types(df, type_spec)

Binary conversion::

    from episia.data.types import convert_to_binary

    # Convert various representations to 0/1
    series = pd.Series(['Yes', 'No', 'Yes', 'No'])
    binary = convert_to_binary(series)  # Returns [1, 0, 1, 0]

Automatic column type detection::

    from episia.data.types import detect_column_types

    types = detect_column_types(df)
    print(types)
    # {'age': 'continuous', 'cases': 'continuous', 'district': 'categorical'}
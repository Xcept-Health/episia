io Module
=========

Input/output functions for epidemiological data.

This module provides functions for reading and writing epidemiological
data in various formats with automatic format detection and validation.

Functions
---------

.. autofunction:: episia.data.io.read_csv
.. autofunction:: episia.data.io.read_excel
.. autofunction:: episia.data.io.read_parquet
.. autofunction:: episia.data.io.from_pandas
.. autofunction:: episia.data.io.from_dict
.. autofunction:: episia.data.io.from_records
.. autofunction:: episia.data.io.read_surveillance_format
.. autofunction:: episia.data.io.detect_format
.. autofunction:: episia.data.io.export_dataset

Examples
--------

Reading data::

    from episia.data.io import read_csv, read_excel, from_pandas

    # Read CSV
    ds = read_csv("surveillance_data.csv")

    # Read Excel
    ds = read_excel("surveillance_data.xlsx", sheet_name="Weekly")

    # Create from pandas DataFrame
    import pandas as pd
    df = pd.DataFrame({'cases': [10, 20, 30]})
    ds = from_pandas(df)

    # Create from dictionary
    data = {'date': ['2023-01-01', '2023-01-02'], 'cases': [10, 15]}
    ds = from_dict(data)

Exporting data::

    from episia.data.io import export_dataset

    # Export to CSV
    export_dataset(ds, "output.csv")

    # Export to Excel with options
    export_dataset(ds, "output.xlsx", sheet_name="Results", index=False)

Format detection::

    from episia.data.io import detect_format

    fmt = detect_format("data.csv")  # Returns 'csv'
    fmt = detect_format("data.xlsx")  # Returns 'excel'
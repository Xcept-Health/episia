dataset Module
==============

Core dataset class for epidemiological data management.

This module provides the :class:`Dataset` class, a pandas DataFrame wrapper
optimized for epidemiological analysis with additional functionality
for cleaning, transforming, and analyzing public health data.

Class
-----

.. autoclass:: episia.data.dataset.Dataset
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __len__, __repr__, __getitem__, __setitem__

Examples
--------

Creating a Dataset::

    from episia.data.dataset import Dataset
    import pandas as pd

    # From DataFrame
    df = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'cases': [10, 15, 20],
        'deaths': [0, 1, 2]
    })
    ds = Dataset(df)

    # From file
    ds = Dataset("surveillance_data.csv")

Data cleaning and optimization::

    # Optimize memory usage
    ds.optimize_types()

    # Clean missing values
    ds.clean(drop_na=True, drop_duplicates=True)

    # Filter data
    ds_filtered = ds.filter("cases > 10")

Epidemiological analysis::

    # Create 2x2 contingency table
    table = ds.create_2x2_table(exposure_col='exposed', outcome_col='case')

    # Calculate incidence
    incidence = ds.calculate_incidence(cases_col='cases', population_col='population')

    # Get epidemiological description
    summary = ds.describe_epidemiological()

History tracking::

    # View transformation history
    history_df = ds.get_history()
    print(history_df)

Export::

    ds.to_csv("output.csv")
    ds.to_parquet("output.parquet")
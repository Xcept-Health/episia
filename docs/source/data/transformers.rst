transformers Module
===================

Data transformation utilities for epidemiological analysis.

This module provides transformer classes and functions for cleaning,
normalizing, and preparing epidemiological data for analysis, with
scikit-learn compatible interfaces.

Classes
-------

.. autoclass:: episia.data.transformers.EpidemiologicalTransformer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.transformers.DateTransformer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.transformers.CategoricalTransformer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.transformers.OutlierTransformer
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.transformers.FeatureEngineer
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: episia.data.transformers.create_pipeline
.. autofunction:: episia.data.transformers.normalize_data

Examples
--------

Date transformation::

    from episia.data.transformers import DateTransformer

    transformer = DateTransformer(date_columns=['date_col'], extract_features=True)
    df_transformed = transformer.fit_transform(df)
    # New columns: date_col_year, date_col_month, date_col_day, etc.

Categorical encoding::

    from episia.data.transformers import CategoricalTransformer

    transformer = CategoricalTransformer(
        categorical_columns=['district', 'disease'],
        encoding='onehot'
    )
    df_encoded = transformer.fit_transform(df)

Outlier handling::

    from episia.data.transformers import OutlierTransformer

    transformer = OutlierTransformer(
        numeric_columns=['age', 'bmi'],
        method='iqr',
        threshold=1.5,
        action='clip'
    )
    df_cleaned = transformer.fit_transform(df)

Feature engineering::

    from episia.data.transformers import FeatureEngineer

    transformer = FeatureEngineer()
    df_features = transformer.fit_transform(df)
    # Creates age_groups, bmi categories, interaction terms

Pipeline creation::

    from episia.data.transformers import create_pipeline, DateTransformer, CategoricalTransformer

    pipeline = create_pipeline([
        DateTransformer(date_columns=['date']),
        CategoricalTransformer(categorical_columns=['district']),
        OutlierTransformer(numeric_columns=['cases'])
    ])

    df_processed = pipeline(df)

Normalization::

    from episia.data.transformers import normalize_data

    df_norm = normalize_data(df, columns=['age', 'bmi'], method='standard')
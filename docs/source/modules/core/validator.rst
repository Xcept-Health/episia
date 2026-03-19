validator Module
================

Data validation functions for ensuring data quality in epidemiological analyses.

This module provides comprehensive validation functions to prevent common errors
and ensure data meets required standards.

Exceptions
----------

.. autoexception:: episia.core.validator.ValidationError

Functions
---------

.. autofunction:: episia.core.validator.validate_2x2_table
.. autofunction:: episia.core.validator.validate_proportion
.. autofunction:: episia.core.validator.validate_confidence_level
.. autofunction:: episia.core.validator.validate_sample_size
.. autofunction:: episia.core.validator.validate_dataframe
.. autofunction:: episia.core.validator.validate_binary_variable
.. autofunction:: episia.core.validator.validate_date_series
.. autofunction:: episia.core.validator.validate_numeric_array
.. autofunction:: episia.core.validator.validate_model_parameters
.. autofunction:: episia.core.validator.check_convergence
.. autofunction:: episia.core.validator.validate_positive

Examples
--------

Validating a 2x2 contingency table::

    from episia.core.validator import validate_2x2_table
    
    # Valid table
    a, b, c, d = validate_2x2_table(40, 10, 20, 30)
    
    # This would raise ValidationError
    # validate_2x2_table(-1, 10, 20, 30)  # Negative value

Validating a proportion::

    from episia.core.validator import validate_proportion
    
    p = validate_proportion(0.75, name="attack rate")
    # p = validate_proportion(1.2)  # Would raise error

Validating a DataFrame::

    import pandas as pd
    from episia.core.validator import validate_dataframe
    
    df = pd.DataFrame({'cases': [10, 20, 30], 'date': ['2023-01-01', '2023-01-02', '2023-01-03']})
    df = validate_dataframe(df, required_columns=['cases', 'date'])
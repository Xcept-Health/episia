utilities Module
================

Helper functions, decorators, and utilities used throughout the Episia package.

This module provides common utility functions for data manipulation,
formatting, type checking, and terminal animations.

Decorators
----------

.. autofunction:: episia.core.utilities.timer
.. autofunction:: episia.core.utilities.validate_input
.. autofunction:: episia.core.utilities.deprecated
.. autofunction:: episia.core.utilities.memoize

Data Utilities
--------------

.. autofunction:: episia.core.utilities.safe_divide
.. autofunction:: episia.core.utilities.clip_values
.. autofunction:: episia.core.utilities.format_number
.. autofunction:: episia.core.utilities.format_pvalue
.. autofunction:: episia.core.utilities.create_bins

Statistical Utilities
---------------------

.. autofunction:: episia.core.utilities.logit
.. autofunction:: episia.core.utilities.expit
.. autofunction:: episia.core.utilities.standardize
.. autofunction:: episia.core.utilities.winsorize

Context Managers
----------------

.. autofunction:: episia.core.utilities.numpy_errstate
.. autofunction:: episia.core.utilities.pandas_display_options

Type Checking
-------------

.. autofunction:: episia.core.utilities.is_numeric
.. autofunction:: episia.core.utilities.is_integer_array
.. autofunction:: episia.core.utilities.is_binary_array

File Utilities
--------------

.. autofunction:: episia.core.utilities.sanitize_filename

Random Utilities
----------------

.. autofunction:: episia.core.utilities.set_random_seed
.. autofunction:: episia.core.utilities.generate_random_id

Terminal Animation
------------------

.. autoclass:: episia.core.utilities.EpiLoader
   :members:
   :undoc-members:
   :show-inheritance:

.. autodata:: episia.core.utilities.Spinner
   :annotation: = EpiLoader

Examples
--------

Using decorators::

    from episia.core.utilities import timer, deprecated
    
    @timer
    def slow_function():
        # This will print execution time
        time.sleep(1)
    
    @deprecated(version="0.2.0", replacement="new_function")
    def old_function():
        pass

Using data utilities::

    from episia.core.utilities import safe_divide, format_pvalue
    
    # Safe division
    result = safe_divide(10, 0, default=float('inf'))
    
    # Format p-value
    p_str = format_pvalue(0.0005)  # Returns "<0.001"

Using context managers::

    from episia.core.utilities import numpy_errstate
    
    with numpy_errstate(divide='ignore', invalid='ignore'):
        result = np.divide(a, b)  # No warnings

Terminal animation::

    from episia.core.utilities import EpiLoader
    
    with EpiLoader("Running SEIR model"):
        result = model.run()  # Shows animated progress
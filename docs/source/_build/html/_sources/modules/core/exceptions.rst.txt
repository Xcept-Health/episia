exceptions Module
=================

Custom exception classes for specific error conditions in epidemiological analysis.

This module defines a hierarchy of exceptions that provide precise error
information for different failure modes.

Exception Hierarchy
-------------------

- :class:`EpisiaError` (base class)
  - :class:`ValidationError`
  - :class:`ConvergenceError`
  - :class:`ConfigurationError`
  - :class:`DataError`
  - :class:`ModelError`
  - :class:`StatisticalError`
  - :class:`DimensionError`
  - :class:`ParameterError`
  - :class:`ComputationError`
  - :class:`FileError`
  - :class:`PlotError`

Classes
-------

.. autoclass:: episia.core.exceptions.EpisiaError
   :members:
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ValidationError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ConvergenceError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ConfigurationError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.DataError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ModelError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.StatisticalError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.DimensionError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ParameterError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.ComputationError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.FileError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.PlotError
   :show-inheritance:

.. autoclass:: episia.core.exceptions.WarningManager
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Using exceptions for error handling::

    from episia.core.exceptions import ValidationError, WarningManager
    
    try:
        # Some validation that might fail
        validate_2x2_table(-1, 10, 20, 30)
    except ValidationError as e:
        print(f"Validation failed: {e}")
    
    # Managing warnings
    WarningManager.warn("This is a warning message")
    WarningManager.filter_warnings("ignore")  # Suppress Episia warnings
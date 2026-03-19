calculator Module
=================

Optimized calculator classes with caching for epidemiological computations.

This module provides cached calculator implementations that improve performance
for repeated calculations and provide consistent interfaces.

Classes
-------

.. autoclass:: episia.core.calculator.CacheStrategy
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.calculator.CalculationStats
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.calculator.BaseCalculator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.calculator.EpidemiologicalCalculator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.calculator.MatrixCalculator
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: episia.core.calculator.cached_function

Singleton Instances
-------------------

.. autodata:: episia.core.calculator.epi_calculator
   :annotation: = EpidemiologicalCalculator()

.. autodata:: episia.core.calculator.matrix_calculator
   :annotation: = MatrixCalculator()

Examples
--------

Basic usage of epidemiological calculator::

    from episia.core.calculator import epi_calculator
    
    # Calculate risk ratio with automatic caching
    rr = epi_calculator.risk_ratio(a=40, b=10, c=20, d=30)
    
    # View performance statistics
    print(f"Cache hit rate: {epi_calculator.stats.cache_hit_rate:.1f}%")

Using cached function decorator::

    from episia.core.calculator import cached_function
    
    @cached_function(maxsize=100)
    def expensive_computation(x, y):
        # Expensive calculation here
        return x ** y
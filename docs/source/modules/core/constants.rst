constants Module
================

Constants used throughout Episia, including statistical thresholds,
default parameters, and configuration options.

Enumerations
------------

.. autoclass:: episia.core.constants.ConfidenceLevel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.AlphaLevel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.PowerLevel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.ConfidenceIntervalMethod
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.RiskRatioMethod
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.OddsRatioMethod
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.PlotStyle
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.core.constants.ColorPalette
   :members:
   :undoc-members:
   :show-inheritance:

Default Values
--------------

.. autodata:: episia.core.constants.DEFAULT_CONFIDENCE
.. autodata:: episia.core.constants.DEFAULT_ALPHA
.. autodata:: episia.core.constants.DEFAULT_POWER
.. autodata:: episia.core.constants.EPSILON
.. autodata:: episia.core.constants.MAX_ITERATIONS
.. autodata:: episia.core.constants.CONVERGENCE_TOL
.. autodata:: episia.core.constants.CHI_SQUARE_SMALL_SAMPLE
.. autodata:: episia.core.constants.FISHER_EXACT_THRESHOLD
.. autodata:: episia.core.constants.NORMAL_APPROXIMATION_N
.. autodata:: episia.core.constants.MEAN_INCUBATION_COVID
.. autodata:: episia.core.constants.MEAN_INFECTIOUS_PERIOD_COVID
.. autodata:: episia.core.constants.BASIC_REPRODUCTION_COVID
.. autodata:: episia.core.constants.WHO_STANDARD_POPULATION
.. autodata:: episia.core.constants.EUROPEAN_STANDARD_POPULATION
.. autodata:: episia.core.constants.DEFAULT_FIGSIZE
.. autodata:: episia.core.constants.DEFAULT_DPI
.. autodata:: episia.core.constants.DEFAULT_FONTSIZE
.. autodata:: episia.core.constants.DEFAULT_COLOR_PALETTE
.. autodata:: episia.core.constants.DEFAULT_PLOT_STYLE

Disease-Specific Parameters
---------------------------

.. autodata:: episia.core.constants.COVID19_PARAMS
.. autodata:: episia.core.constants.INFLUENZA_PARAMS
.. autodata:: episia.core.constants.EBOLA_PARAMS

Configuration
-------------

.. autodata:: episia.core.constants.EPISIA_CONFIG

.. autofunction:: episia.core.constants.get_config
.. autofunction:: episia.core.constants.set_config
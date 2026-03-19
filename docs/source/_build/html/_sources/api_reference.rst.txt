API Reference
=============

The Episia API is organized into several modules. The recommended way to use Episia
is through the unified ``epi`` interface:

.. code-block:: python

    from episia import epi

For advanced usage, you can import specific modules directly:

.. code-block:: python

    from episia.models import SEIRModel, SensitivityAnalysis
    from episia.stats import risk_ratio, roc_analysis
    from episia.data import SurveillanceDataset
    from episia.viz import plot_epicurve, set_theme

Module Overview
---------------

- :doc:`modules/stats/index` - Statistical methods for epidemiology
- :doc:`modules/viz/index` - Visualization tools
- :doc:`modules/dhis2/index` - DHIS2 integration
- :doc:`modules/data/index` - Data management
- :doc:`modules/core/index` - Core utilities
- :doc:`modules/models/index` - Epidemic models
- :doc:`modules/api/reporting` - Report generation
- :doc:`modules/api/results` - Result objects
- :doc:`modules/api/unified` - Unified interface

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules/index
results Module
==============

Unified rich result classes for Episia public API.

This module provides a consistent result interface across all Episia modules.
Every public function returns a subclass of :class:`EpiResult`, ensuring
consistent serialization and visualization.

Base Classes
------------

.. autoclass:: episia.api.results.EpiResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.ConfidenceInterval
   :members:
   :undoc-members:
   :show-inheritance:

Result Classes
--------------

.. autoclass:: episia.api.results.AssociationResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.ProportionResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.SampleSizeResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.DiagnosticResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.ROCResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.StratifiedResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.ModelResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.TimeSeriesResult
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.api.results.RegressionResult
   :members:
   :undoc-members:
   :show-inheritance:

Factory Functions
-----------------

.. autofunction:: episia.api.results.make_ci
.. autofunction:: episia.api.results.make_association
.. autofunction:: episia.api.results.make_proportion
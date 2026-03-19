dhis2 Module
============

Optional DHIS2 integration module for Episia.

This module provides tools for connecting to DHIS2 instances, fetching
surveillance data, and converting it to Episia's :class:`~episia.data.surveillance.SurveillanceDataset`
format for immediate epidemiological analysis.

.. note::

   This module requires additional dependencies. Install with:
   
   .. code-block:: bash

      pip install episia[dhis2]

.. toctree::
   :maxdepth: 2
   :caption: DHIS2 Submodules:

   client
   adapter
   constants
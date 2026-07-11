dhis2 Module
============

Optional DHIS2 integration module for Episia.

This module provides tools for connecting to DHIS2 instances
(:doc:`client`), fetching surveillance data, converting it to Episia's
:class:`~episia.data.surveillance.SurveillanceDataset` format
(:doc:`adapter`) for immediate epidemiological analysis, and building the
period-range strings the DHIS2 analytics API expects (:doc:`periods`).

.. note::

   This module requires additional dependencies. Install with:
   
   .. code-block:: bash

      pip install episia[dhis2]

.. toctree::
   :maxdepth: 2
   :caption: DHIS2 Submodules:

   client
   adapter
   periods
   constants
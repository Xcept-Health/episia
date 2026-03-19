constants Module
================

Constants for DHIS2 integration.

This module provides endpoint definitions, field mappings, and preset
data element UIDs for common WHO/AFRO notifiable diseases.

API Endpoints
-------------

.. autodata:: episia.dhis2.constants.ENDPOINTS
   :annotation:

Standard field mappings
-----------------------

.. autodata:: episia.dhis2.constants.ANALYTICS_FIELDS
   :annotation:

Period type mappings
--------------------

.. autodata:: episia.dhis2.constants.PERIOD_TYPES
   :annotation:

WHO/AFRO data elements
----------------------

.. autodata:: episia.dhis2.constants.WHO_AFRO_ELEMENTS
   :annotation:

   Common data element UIDs for the WHO African Region:

   - ``malaria_confirmed``: Confirmed malaria cases
   - ``malaria_deaths``: Malaria deaths
   - ``meningitis_cases``: Meningitis cases
   - ``cholera_cases``: Cholera cases
   - ``measles_cases``: Measles cases

Usage Examples
--------------

Using endpoints::

    from episia.dhis2.constants import ENDPOINTS

    # Build API URLs
    analytics_url = f"https://your-dhis2.org{ENDPOINTS['analytics']}"
    print(analytics_url)  # /api/analytics

Using WHO AFRO elements::

    from episia.dhis2.constants import WHO_AFRO_ELEMENTS
    from episia.dhis2 import DHIS2Client

    client = DHIS2Client(url="...", username="...", password="...")

    # Fetch malaria data using preset UIDs
    ds = client.to_dataset(
        data_element=WHO_AFRO_ELEMENTS["malaria_confirmed"],
        deaths_element=WHO_AFRO_ELEMENTS["malaria_deaths"],
        period="LAST_52_WEEKS",
        org_unit="ImspTQPwCqd"
    )

Custom period expressions::

    from episia.dhis2.constants import PERIOD_TYPES

    # Map Episia frequency to DHIS2 period type
    freq = "W"  # Episia weekly
    dhis2_period_type = PERIOD_TYPES.get("weekly", "W")
    
    # Build period expression
    period = f"2024W01:2024W52"
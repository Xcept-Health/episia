adapter Module
==============

Convert DHIS2 API responses to Episia datasets.

This module provides the :class:`DHIS2Adapter` class for converting raw
DHIS2 API responses into Episia's :class:`~episia.data.surveillance.SurveillanceDataset`
format.

Class
-----

.. autoclass:: episia.dhis2.adapter.DHIS2Adapter
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Using the adapter standalone::

    from episia.dhis2 import DHIS2Adapter
    import json

    # Load previously fetched DHIS2 data
    with open("dhis2_response.json") as f:
        response = json.load(f)

    adapter = DHIS2Adapter()

    # Convert to SurveillanceDataset
    ds = adapter.from_analytics_response(
        response,
        cases_element="FTRrcoaog83",
        deaths_element="cYeuwXTCPkU"
    )

    print(ds)

Working with dataValueSets::

    # Convert dataValueSets response to DataFrame
    with open("data_values.json") as f:
        data_values = json.load(f)

    df = adapter.from_data_value_sets(data_values)
    print(df.head())

Period parsing::

    # The adapter handles various DHIS2 period formats
    from episia.dhis2.adapter import DHIS2Adapter
    import pandas as pd

    adapter = DHIS2Adapter()
    
    series = pd.Series(["2024W01", "202401", "2024Q1", "2024"])
    parsed = adapter._parse_dhis2_period(series)
    print(parsed)
    # Output: Timestamps for week 1 of 2024, Jan 2024, Jan 2024, Jan 2024
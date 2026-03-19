client Module
=============

DHIS2 REST API client for Episia.

This module provides the :class:`DHIS2Client` class for connecting to DHIS2
instances, fetching surveillance data, and converting it to Episia's
:class:`~episia.data.surveillance.SurveillanceDataset` format.

Class
-----

.. autoclass:: episia.dhis2.client.DHIS2Client
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __repr__

Examples
--------

Basic connection and data fetching::

    from episia.dhis2 import DHIS2Client

    # Connect to DHIS2 demo instance
    client = DHIS2Client(
        url      = "https://play.dhis2.org/40.2.2",
        username = "admin",
        password = "district",
    )

    # Test connection
    if client.ping():
        print("Connected successfully!")

    # Fetch data as SurveillanceDataset
    ds = client.to_dataset(
        data_element = "FTRrcoaog83",  # Malaria cases
        period       = "LAST_52_WEEKS",
        org_unit     = "ImspTQPwCqd",   # Sierra Leone
    )

    print(f"Total cases: {ds.total_cases}")
    ds.to_timeseries_result().plot().show()

Fetching with deaths data::

    ds = client.to_dataset(
        data_element   = "FTRrcoaog83",   # Cases
        deaths_element = "cYeuwXTCPkU",   # Deaths
        period         = "2024W01:2024W52",
        org_unit       = "ImspTQPwCqd",
    )

    print(f"CFR: {ds.cfr:.1%}")

District-level data::

    # Fetch data for all districts under the national level
    ds = client.to_dataset_by_district(
        data_element = "FTRrcoaog83",
        period       = "2024W01:2024W52",
        org_unit     = "ImspTQPwCqd",   # National level
    )

    # Now dataset has district column
    for district in ds.districts:
        district_ds = ds.filter_district(district)
        print(f"{district}: {district_ds.total_cases} cases")

Advanced usage with raw API calls::

    # List organisation units
    org_units = client.list_org_units(level=2)  # Regions
    for ou in org_units:
        print(f"{ou['name']}: {ou['id']}")

    # List data elements
    elements = client.list_data_elements()
    for elem in elements[:5]:  # First 5
        print(f"{elem['name']}: {elem['id']}")

    # Raw analytics fetch
    raw_data = client.fetch_analytics(
        data_elements = ["FTRrcoaog83", "cYeuwXTCPkU"],
        period        = "2024W01:2024W52",
        org_unit      = "ImspTQPwCqd",
    )
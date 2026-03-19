"""
episia.dhis2 - Optional DHIS2 integration module.

Install with: pip install episia[dhis2]

Provides:
    DHIS2Client     REST API client for DHIS2 instances
    DHIS2Adapter    converts DHIS2 responses to SurveillanceDataset

Usage::

    from episia.dhis2 import DHIS2Client

    client = DHIS2Client(
        url      = "https://hmis.sante.bf",
        username = "admin",
        password = "district",
    )

    ds = client.to_dataset(
        data_element = "FTRrcoaog83",
        period       = "2024W01:2024W52",
        org_unit     = "ImspTQPwCqd",
    )
    print(ds)
"""

from .client  import DHIS2Client
from .adapter import DHIS2Adapter

__all__ = ["DHIS2Client", "DHIS2Adapter"]
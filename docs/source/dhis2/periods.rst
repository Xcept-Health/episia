periods Module
===============

DHIS2 period-string helpers.

DHIS2's analytics API expects periods as compact strings (e.g.
``"202401"`` for January 2024) and period *ranges* as semicolon-separated
lists of those strings (e.g. ``"202401;202402;202403"``). This module
builds those ranges for you so you never have to hand-roll date math
when requesting surveillance data.

Supported formats
------------------

- **Monthly** — ``YYYYMM``, e.g. ``"202401"``
- **Weekly** — ``YYYYWnn`` (ISO 8601 week numbering), e.g. ``"2024W01"``
- **Quarterly** — ``YYYYQn``, e.g. ``"2024Q1"``

*Start* and *end* must use the same format; ``period_range`` raises
``ValueError`` if they don't, if the format isn't recognised, or if
*start* is chronologically after *end*.

Functions
---------

.. autofunction:: episia.dhis2.periods.period_range

Examples
--------

Monthly range for a full year::

    from episia.dhis2.periods import period_range

    periods = period_range("202401", "202412")
    print(periods)
    # "202401;202402;202403;202404;202405;202406;202407;202408;202409;202410;202411;202412"

Weekly range (ISO weeks)::

    period_range("2024W01", "2024W04")
    # "2024W01;2024W02;2024W03;2024W04"

Quarterly range::

    period_range("2024Q1", "2024Q4")
    # "2024Q1;2024Q2;2024Q3;2024Q4"

Using it with the DHIS2 client to fetch a full year of monthly malaria
case counts::

    from episia.dhis2 import DHIS2Client
    from episia.dhis2.periods import period_range

    client = DHIS2Client(
        url      = "https://play.dhis2.org/40.2.2",
        username = "admin",
        password = "district",
    )

    raw_data = client.fetch_analytics(
        data_elements = ["FTRrcoaog83"],           # malaria confirmed cases
        period        = period_range("202401", "202412"),
        org_unit      = "ImspTQPwCqd",              # Sierra Leone
    )

``period_range`` is what lets you build that ``period`` string without
manually listing twelve month codes, and it works the same way for the
``period=`` argument of :meth:`~episia.dhis2.client.DHIS2Client.to_dataset`.
See :doc:`client` for the full ``DHIS2Client`` API and :doc:`adapter` for
converting the response into an Episia
:class:`~episia.data.surveillance.SurveillanceDataset`.

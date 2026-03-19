surveillance Module
===================

Epidemiological surveillance data utilities.

This module provides tools for ingesting, cleaning, aggregating, and alerting on
routine surveillance data, designed for public health contexts.

Classes
-------

.. autoclass:: episia.data.surveillance.SurveillanceDataset
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.surveillance.AlertEngine
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.data.surveillance.Alert
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: episia.data.surveillance.from_dhis2_csv
.. autofunction:: episia.data.surveillance.compute_attack_rate
.. autofunction:: episia.data.surveillance.endemic_channel
.. autofunction:: episia.data.surveillance.aggregate_by

Examples
--------

Creating a surveillance dataset::

    from episia.data.surveillance import SurveillanceDataset

    # From CSV
    ds = SurveillanceDataset.from_csv(
        "meningite_2024.csv",
        date_col="semaine",
        cases_col="cas",
        district_col="district",
        disease_col="maladie"
    )

    # Basic information
    print(f"Total cases: {ds.total_cases}")
    print(f"Date range: {ds.date_range}")
    print(f"Districts: {ds.districts}")

Data aggregation::

    # Aggregate weekly
    weekly = ds.aggregate(freq="W")

    # Aggregate by district and week
    stratified = ds.aggregate(freq="W", group_by=["district"])

Epidemiological metrics::

    # Attack rate
    ar = ds.attack_rate(population=1000000, per=100000)

    # Weekly attack rates
    weekly_ar = ds.weekly_attack_rates(population=1000000)

    # Endemic channel
    channel = ds.endemic_channel(historical_years=[2020, 2021, 2022])
    print(f"P75 threshold: {channel['p_high']}")

Alert detection::

    # Create alert engine
    engine = AlertEngine(ds)

    # Run alerts
    alerts = engine.run(
        threshold=50,
        zscore_threshold=2.0,
        use_endemic_channel=True
    )

    for alert in alerts:
        print(f"{alert.period}: {alert.severity} - {alert.message}")

    # Alert summary
    summary = engine.alert_summary(alerts)
    print(f"Alerts by severity: {summary['severity_counts']}")

DHIS2 integration::

    from episia.data.surveillance import from_dhis2_csv

    # Load DHIS2 export
    ds = from_dhis2_csv("dhis2_export.csv")
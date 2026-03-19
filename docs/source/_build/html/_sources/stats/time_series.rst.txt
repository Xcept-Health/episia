time_series Module
==================

Temporal analysis of epidemiological data.

This module provides functions for analyzing temporal patterns in
epidemiological data, including epidemic curves, incidence rates,
and temporal trend analysis.

Classes
-------

.. autoclass:: episia.stats.time_series.TimeAggregation
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.time_series.TrendMethod
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.time_series.EpidemicCurve
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.time_series.TimeSeriesResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.time_series.calculate_incidence
.. autofunction:: episia.stats.time_series.calculate_attack_rate
.. autofunction:: episia.stats.time_series.epidemic_curve
.. autofunction:: episia.stats.time_series.moving_average
.. autofunction:: episia.stats.time_series.loess_smoothing
.. autofunction:: episia.stats.time_series.detect_epidemic_threshold
.. autofunction:: episia.stats.time_series.reproductive_number
.. autofunction:: episia.stats.time_series.seasonality_decomposition
.. autofunction:: episia.stats.time_series.exponential_growth_rate
.. autofunction:: episia.stats.time_series.nowcasting
.. autofunction:: episia.stats.time_series.cumulative_curve
.. autofunction:: episia.stats.time_series.detect_peaks

Examples
--------

Creating an epidemic curve::

    import pandas as pd
    from episia.stats.time_series import epidemic_curve, TimeAggregation

    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    cases = np.random.poisson(lam=5, size=100)

    curve = epidemic_curve(dates, cases, aggregation=TimeAggregation.WEEKLY)
    print(curve.summary())

    # Convert to DataFrame for analysis
    df = curve.to_dataframe()

Moving average smoothing::

    from episia.stats.time_series import moving_average

    smoothed = moving_average(cases, window=7)
    
    # 7-day moving average
    for i, (orig, smooth) in enumerate(zip(cases[:10], smoothed[:10])):
        print(f"Day {i+1}: {orig} → {smooth:.1f}")

Detecting epidemic threshold::

    from episia.stats.time_series import detect_epidemic_threshold

    result = detect_epidemic_threshold(
        cases,
        method='moving_average',
        window=7,
        multiplier=2.0
    )

    print(f"Threshold: {result['threshold']:.1f}")
    print(f"Epidemic days: {result['epidemic_days']}")

Time-varying reproductive number::

    from episia.stats.time_series import reproductive_number

    Rt = reproductive_number(cases, serial_interval=5.0, method='cori')
    for day, rt in enumerate(Rt[:30]):
        if rt > 0:
            print(f"Day {day+1}: Rt={rt:.2f}")

Exponential growth rate::

    from episia.stats.time_series import exponential_growth_rate

    growth = exponential_growth_rate(cases[:30])
    print(f"Growth rate: {growth['growth_rate']:.3f} per day")
    print(f"Doubling time: {growth['doubling_time']:.1f} days")
    print(f"R²: {growth['r_squared']:.3f}")

Seasonality decomposition::

    from episia.stats.time_series import seasonality_decomposition

    # Annual data with weekly cases
    weekly_cases = np.random.poisson(lam=10, size=104)  # 2 years
    decomp = seasonality_decomposition(weekly_cases, period=52, model='additive')

    # Access components
    trend = decomp['trend']
    seasonal = decomp['seasonal']
    residual = decomp['residual']

Peak detection::

    from episia.stats.time_series import detect_peaks

    peaks = detect_peaks(cases, distance=7, prominence=10)
    print(f"Found {peaks['n_peaks']} peaks at indices: {peaks['peak_indices']}")
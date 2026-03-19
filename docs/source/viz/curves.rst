curves Module
=============

Epidemic curve and trend visualizations.

This module provides functions for plotting epidemic curves, incidence rates,
trend lines, and growth curves with doubling time annotations.

Functions
---------

.. autofunction:: episia.viz.curves.plot_epicurve
.. autofunction:: episia.viz.curves.plot_trend
.. autofunction:: episia.viz.curves.plot_incidence
.. autofunction:: episia.viz.curves.plot_doubling

Examples
--------

Basic epidemic curve::

    from episia.viz.curves import plot_epicurve
    from episia.stats.time_series import epidemic_curve

    # Create epidemic curve from case data
    curve = epidemic_curve(dates, cases, aggregation='weekly')
    
    # Plot with default settings
    fig = plot_epicurve(curve, title="Weekly COVID-19 Cases")
    fig.show()

Animated epidemic curve::

    # Animated version (bars build up)
    fig = plot_epicurve(
        curve,
        title="Epidemic Progression",
        animate=True,
        backend="plotly"
    )
    fig.show()

Trend analysis::

    from episia.viz.curves import plot_trend

    fig = plot_trend(
        result,  # TimeSeriesResult object
        show_observed=True,
        title="Incidence Trend with LOESS Smoothing"
    )

Incidence rates with confidence bands::

    from episia.viz.curves import plot_incidence

    fig = plot_incidence(
        times=weeks,
        rates=incidence_rates,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        per=100000,
        title="Weekly Incidence Rate per 100,000"
    )

Doubling time plot::

    from episia.viz.curves import plot_doubling

    fig = plot_doubling(
        times=days[:30],
        values=cumulative_cases[:30],
        doubling_time=3.2,
        title="Early Exponential Growth",
        ylabel="Cumulative Cases (log scale)"
    )
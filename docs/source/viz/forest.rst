forest Module
=============

Forest plot visualizations.

This module provides functions for creating forest plots for stratified
analysis, meta-analysis, and regression results.

Functions
---------

.. autofunction:: episia.viz.forest.plot_forest
.. autofunction:: episia.viz.forest.plot_meta_forest

Examples
--------

Stratified analysis forest plot::

    from episia.stats.stratified import mantel_haenszel_or
    from episia.viz.forest import plot_forest

    # Perform Mantel-Haenszel analysis
    mh_result = mantel_haenszel_or(stratified_tables)

    # Forest plot with strata
    fig = plot_forest(
        mh_result,
        title="Stratified Analysis by Age Group"
    )
    fig.show()

Regression forest plot::

    from episia.viz.forest import plot_forest

    fig = plot_forest(
        regression_result,  # From logistic_regression()
        title="Logistic Regression - Odds Ratios"
    )

Meta-analysis forest plot::

    from episia.viz.forest import plot_meta_forest

    # Study-level data
    estimates = [1.2, 1.5, 1.8, 1.3]
    ci_lowers = [0.9, 1.1, 1.4, 1.0]
    ci_uppers = [1.5, 1.9, 2.2, 1.6]
    labels = ["Study 1", "Study 2", "Study 3", "Study 4"]
    weights = [25, 30, 20, 25]  # Study weights (e.g., sample size)

    fig = plot_meta_forest(
        estimates,
        ci_lowers,
        ci_uppers,
        labels,
        weights=weights,
        pooled_estimate=1.45,
        pooled_ci=(1.25, 1.65),
        i_squared=35.2,
        p_heterogeneity=0.042,
        title="Meta-Analysis of Intervention Effect"
    )
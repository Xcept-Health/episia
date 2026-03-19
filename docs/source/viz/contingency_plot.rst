contingency_plot Module
=======================

2x2 contingency table visualizations.

This module provides functions for visualizing 2x2 contingency tables
with annotated heatmaps and summary metrics.

Functions
---------

.. autofunction:: episia.viz.contingency_plot.plot_contingency
.. autofunction:: episia.viz.contingency_plot.plot_measures

Examples
--------

Contingency table heatmap::

    from episia.stats.contingency import Table2x2
    from episia.viz.contingency_plot import plot_contingency

    table = Table2x2(a=40, b=10, c=20, d=30)
    fig = plot_contingency(
        table,
        title="Exposure X Disease Association"
    )
    fig.show()

Comparison of all measures::

    from episia.viz.contingency_plot import plot_measures

    fig = plot_measures(
        table,
        title="Association Measures with 95% CI",
        backend="matplotlib"  # Publication quality
    )
    
    # Subset of measures
    fig = plot_measures(
        table,
        measures=["Risk Ratio", "Odds Ratio"],
        title="Key Effect Measures"
    )
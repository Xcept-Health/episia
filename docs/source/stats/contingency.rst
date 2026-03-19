contingency Module
==================

2x2 contingency table calculations for epidemiology.

This module provides the :class:`Table2x2` class for performing epidemiological
calculations on 2x2 contingency tables, including risk ratios, odds ratios,
risk differences, and various confidence intervals.

Classes
-------

.. autoclass:: episia.stats.contingency.Table2x2
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __repr__

.. autoclass:: episia.stats.contingency.RiskRatioResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

.. autoclass:: episia.stats.contingency.OddsRatioResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

.. autoclass:: episia.stats.contingency.ConfidenceMethod
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: episia.stats.contingency.risk_ratio
.. autofunction:: episia.stats.contingency.odds_ratio
.. autofunction:: episia.stats.contingency.from_dataframe

Examples
--------

Creating a 2x2 table::

    from episia.stats.contingency import Table2x2, ConfidenceMethod

    # Table: Exposed vs Unexposed, Cases vs Non-cases
    table = Table2x2(a=40, b=10, c=20, d=30)

    print(f"Risk in exposed: {table.risk_exposed:.3f}")
    print(f"Risk in unexposed: {table.risk_unexposed:.3f}")

Risk ratio calculation::

    # Risk ratio with Wald confidence interval
    rr = table.risk_ratio(method=ConfidenceMethod.WALD, confidence=0.95)
    print(rr)  # Risk Ratio: 2.667 (1.514-4.696)
    print(f"Significant: {rr.significant}")

Odds ratio calculation::

    # Odds ratio with exact confidence interval
    or_result = table.odds_ratio(method=ConfidenceMethod.EXACT)
    print(or_result)  # Odds Ratio: 6.000 (2.241-16.788)

Comprehensive summary::

    summary = table.summary()
    print(f"Chi-square: {summary['chi_square']['chi2']:.3f}")
    print(f"Fisher exact p-value: {summary['fisher_exact']['p_value']:.4f}")

From DataFrame::

    import pandas as pd
    from episia.stats.contingency import from_dataframe

    df = pd.DataFrame({
        'exposed': [1, 1, 0, 0, 1, 0],
        'case': [1, 0, 1, 0, 1, 0]
    })
    table = from_dataframe(df, exposed_col='exposed', outcome_col='case')
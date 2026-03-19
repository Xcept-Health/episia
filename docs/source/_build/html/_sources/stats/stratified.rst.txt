stratified Module
=================

Stratified analysis for confounding and effect modification.

This module provides functions for stratified analysis, including
Mantel-Haenszel methods for adjusting for confounding variables
and testing for effect modification.

Classes
-------

.. autoclass:: episia.stats.stratified.StratifiedMethod
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.stratified.StratifiedTable
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __len__, __getitem__

.. autoclass:: episia.stats.stratified.MantelHaenszelResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

.. autoclass:: episia.stats.stratified.DirectStandardizationResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.stratified.mantel_haenszel_or
.. autofunction:: episia.stats.stratified.test_effect_modification
.. autofunction:: episia.stats.stratified.direct_standardization
.. autofunction:: episia.stats.stratified.indirect_standardization
.. autofunction:: episia.stats.stratified.stratified_by_variable

Examples
--------

Creating stratified tables::

    from episia.stats.contingency import Table2x2
    from episia.stats.stratified import StratifiedTable

    # Two strata (e.g., males and females)
    table1 = Table2x2(a=10, b=20, c=30, d=40)
    table2 = Table2x2(a=15, b=25, c=35, d=45)

    stratified = StratifiedTable(
        tables=[table1, table2],
        strata_names=['Males', 'Females']
    )

Mantel-Haenszel analysis::

    from episia.stats.stratified import mantel_haenszel_or

    mh_result = mantel_haenszel_or(stratified, confidence=0.95)
    print(mh_result)
    print(f"Common OR: {mh_result.common_or:.3f}")
    print(f"95% CI: {mh_result.or_ci[0]:.3f}-{mh_result.or_ci[1]:.3f}")
    print(f"Test for heterogeneity: p={mh_result.q_p_value:.3f}")
    print(f"I² = {mh_result.i_squared:.1f}%")

Testing effect modification::

    from episia.stats.stratified import test_effect_modification

    em_test = test_effect_modification(stratified, method='woolf')
    print(f"Homogeneity test: χ²={em_test['statistic']:.3f}, p={em_test['p_value']:.3f}")

Direct standardization::

    import numpy as np
    from episia.stats.stratified import direct_standardization

    # Age-specific rates, population, standard population
    rates = np.array([0.01, 0.05, 0.10])
    pop = np.array([1000, 800, 500])
    standard = np.array([1000, 1000, 1000])

    result = direct_standardization(rates, pop, standard)
    print(f"Crude rate: {result.crude_rate:.4f}")
    print(f"Adjusted rate: {result.adjusted_rate:.4f}")
    print(f"95% CI: {result.ci[0]:.4f}-{result.ci[1]:.4f}")

Indirect standardization (SMR)::

    from episia.stats.stratified import indirect_standardization

    smr_result = indirect_standardization(
        observed_cases=np.array([10, 15, 5]),
        stratum_populations=np.array([1000, 800, 500]),
        reference_rates=np.array([0.02, 0.03, 0.01])
    )
    print(f"SMR: {smr_result['smr']:.3f}")
    print(f"95% CI: {smr_result['ci_lower']:.3f}-{smr_result['ci_upper']:.3f}")

From DataFrame::

    import pandas as pd
    from episia.stats.stratified import stratified_by_variable

    df = pd.DataFrame({
        'exposed': [1, 1, 0, 0, 1, 0],
        'case': [1, 0, 1, 0, 1, 0],
        'age_group': ['young', 'old', 'young', 'old', 'young', 'old']
    })

    stratified = stratified_by_variable(
        data=df,
        exposure_var='exposed',
        outcome_var='case',
        stratify_var='age_group'
    )
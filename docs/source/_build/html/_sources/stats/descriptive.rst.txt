descriptive Module
==================

Descriptive statistics for epidemiological data.

This module provides functions for calculating confidence intervals
for proportions, means, and other descriptive statistics commonly
used in epidemiological analysis.

Classes
-------

.. autoclass:: episia.stats.descriptive.CI_Method
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.descriptive.ProportionResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

.. autoclass:: episia.stats.descriptive.MeanResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.descriptive.proportion_ci
.. autofunction:: episia.stats.descriptive.mean_ci
.. autofunction:: episia.stats.descriptive.incidence_rate
.. autofunction:: episia.stats.descriptive.attack_rate
.. autofunction:: episia.stats.descriptive.prevalence
.. autofunction:: episia.stats.descriptive.median_ci
.. autofunction:: episia.stats.descriptive.interquartile_range

Examples
--------

Proportion confidence intervals::

    from episia.stats.descriptive import proportion_ci, CI_Method

    # Wilson interval (recommended)
    prop = proportion_ci(45, 100, method=CI_Method.WILSON)
    print(prop)  # Proportion: 0.4500 (0.354-0.549)

    # Wald interval (large samples only)
    prop_wald = proportion_ci(45, 100, method=CI_Method.WALD)
    
    # Exact Clopper-Pearson (conservative)
    prop_exact = proportion_ci(5, 10, method=CI_Method.CLOPPER_PEARSON)

Mean confidence intervals::

    import numpy as np
    from episia.stats.descriptive import mean_ci

    data = np.array([23, 25, 27, 22, 24, 26, 28, 21, 23, 25])
    mean_result = mean_ci(data, confidence=0.95)
    print(mean_result)  # Mean: 24.4000 (22.825-25.975)

Incidence rates::

    from episia.stats.descriptive import incidence_rate

    # 10 cases over 1000 person-years
    ir = incidence_rate(cases=10, person_time=1000)
    print(f"Incidence rate: {ir['rate']:.4f} per person-year")
    print(f"95% CI: {ir['ci_lower']:.4f}-{ir['ci_upper']:.4f}")

Median with confidence interval::

    median_result = median_ci(data, method='exact')
    print(f"Median: {median_result['median']:.1f} "
          f"({median_result['ci_lower']:.1f}-{median_result['ci_upper']:.1f})")
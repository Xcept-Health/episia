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

.. autoclass:: episia.stats.descriptive.IncidenceRateResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.descriptive.proportion_ci
.. autofunction:: episia.stats.descriptive.mean_ci
.. autofunction:: episia.stats.descriptive.incidence_rate
.. autofunction:: episia.stats.descriptive.cumulative_incidence
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

    # 20 seroconversions over 500 person-years, displayed per 100 person-years
    ir = incidence_rate(cases=20, person_time=500, multiplier=100)
    print(ir)                    # Rate: 4.0000 (2.4423-6.1780) per 100 person-time
    print(f"Incidence rate: {ir.rate:.4f} per person-year")
    print(f"95% CI: {ir.ci_lower:.4f}-{ir.ci_upper:.4f}")
    print(ir.to_dict())          # JSON-serialisable dict, handy for reports

``incidence_rate`` returns an :class:`~episia.stats.descriptive.IncidenceRateResult`
object (attribute access, not a dict) — use ``multiplier`` to control the
display scale (e.g. ``100`` or ``100_000``) without changing the stored rate.

Cumulative incidence (attack rate)::

    from episia.stats.descriptive import cumulative_incidence, attack_rate

    # Malaria cohort, rainy season, Sahel: 120 cases in 500 at-risk
    risk = cumulative_incidence(cases=120, population_at_risk=500)
    print(risk)  # Proportion: 0.2400 (0.2046-0.2793)

    # attack_rate() is an epidemiological alias for cumulative_incidence()
    same_result = attack_rate(cases=120, population=500)

Unlike ``incidence_rate`` (a rate over person-time, used for ongoing
surveillance), ``cumulative_incidence`` is a proportion over a fixed
at-risk population — use it when everyone was followed for the same
period and you want to answer "what fraction of the at-risk group got
sick during this outbreak?".

Median with confidence interval::

    median_result = median_ci(data, method='exact')
    print(f"Median: {median_result['median']:.1f} "
          f"({median_result['ci_lower']:.1f}-{median_result['ci_upper']:.1f})")
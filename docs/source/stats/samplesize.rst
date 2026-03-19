samplesize Module
=================

Sample size and power calculations for epidemiological studies.

This module provides functions for calculating required sample sizes
and statistical power for common epidemiological study designs:
cohort studies, case-control studies, cross-sectional studies,
and diagnostic test studies.

Classes
-------

.. autoclass:: episia.stats.samplesize.StudyDesign
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.samplesize.TestType
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.stats.samplesize.SampleSizeResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Functions
---------

.. autofunction:: episia.stats.samplesize.sample_size_risk_ratio
.. autofunction:: episia.stats.samplesize.sample_size_risk_difference
.. autofunction:: episia.stats.samplesize.sample_size_odds_ratio
.. autofunction:: episia.stats.samplesize.sample_size_sensitivity_specificity
.. autofunction:: episia.stats.samplesize.sample_size_single_proportion
.. autofunction:: episia.stats.samplesize.power_calculation
.. autofunction:: episia.stats.samplesize.fleiss_correction
.. autofunction:: episia.stats.samplesize.design_effect_deff
.. autofunction:: episia.stats.samplesize.calculate_sample_size

Examples
--------

Cohort study sample size::

    from episia.stats.samplesize import sample_size_risk_ratio, TestType

    # Detect RR=2.0 with baseline risk=0.1, power=0.8, α=0.05
    result = sample_size_risk_ratio(
        risk_unexposed=0.1,
        risk_ratio=2.0,
        power=0.8,
        alpha=0.05,
        test_type=TestType.TWO_SIDED
    )

    print(result)  # Sample size: 199 per group
    print(f"Total participants needed: {result.n_total:.0f}")

Case-control study::

    from episia.stats.samplesize import sample_size_odds_ratio

    result = sample_size_odds_ratio(
        proportion_exposed_controls=0.3,
        odds_ratio=2.0,
        power=0.8,
        r=2  # Two controls per case
    )

    print(f"Cases needed: {result.n_cases:.0f}")
    print(f"Controls needed: {result.n_controls:.0f}")

Diagnostic test study::

    from episia.stats.samplesize import sample_size_sensitivity_specificity

    result = sample_size_sensitivity_specificity(
        expected_sens=0.9,
        expected_spec=0.85,
        precision=0.05,
        prevalence=0.1
    )

    print(f"Total subjects: {result.n_total:.0f}")

Cross-sectional survey::

    result = sample_size_single_proportion(
        expected_proportion=0.5,
        precision=0.03,
        design_effect=1.5
    )
    print(f"Sample size: {result.n_total:.0f}")

Power calculation::

    from episia.stats.samplesize import power_calculation, StudyDesign

    power_result = power_calculation(
        n_per_group=150,
        risk_unexposed=0.1,
        risk_ratio=2.0,
        design=StudyDesign.COHORT
    )
    print(f"Achieved power: {power_result.power:.3f}")
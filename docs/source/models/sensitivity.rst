sensitivity Module
==================

Monte Carlo sensitivity analysis for compartmental models.

This module provides tools to sample parameter distributions, run thousands
of model instances, and aggregate results into percentile envelopes for
uncertainty quantification.

Classes
-------

.. autoclass:: episia.models.sensitivity.SensitivityAnalysis
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.sensitivity.SensitivityResult
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __repr__

Supported Distributions
-----------------------

- ``('uniform', low, high)``
- ``('normal', mean, std)``
- ``('lognormal', mean, sigma)``  # mean/std of underlying normal
- ``('triangular', low, mode, high)``
- ``('beta_dist', alpha, beta)``
- ``('fixed', value)``  # Pin a parameter

Examples
--------

Basic sensitivity analysis::

    from episia.models import SEIRModel
    from episia.models.parameters import SEIRParameters
    from episia.models.sensitivity import SensitivityAnalysis

    sa = SensitivityAnalysis(
        model_class=SEIRModel,
        param_class=SEIRParameters,
        fixed={
            'N': 1_000_000,
            'I0': 10,
            'E0': 50,
            't_span': (0, 365)
        },
        distributions={
            'beta': ('uniform', 0.25, 0.50),
            'sigma': ('normal', 1/5.2, 0.02),
            'gamma': ('uniform', 1/21, 1/7),
        },
        n_samples=500,
        seed=42,
        n_jobs=-1  # Use all CPU cores
    )

    result = sa.run(verbose=True)

    print(result)  # Summary statistics
    result.plot(compartment='I').show()  # Trajectory envelope
    result.plot_metric_distribution('r0').show()  # R₀ distribution

    # Export to DataFrame
    df = result.to_dataframe()
    print(df.describe())

Interpreting results::

    # Get summary statistics
    summary = result.summary()
    print(f"R₀ median: {summary['r0_median']:.2f} [{summary['r0_p5']:.2f}-{summary['r0_p95']:.2f}]")
    print(f"Peak infections: {summary['peak_infected_median']:.0f} [{summary['peak_infected_p5']:.0f}-{summary['peak_infected_p95']:.0f}]")

    # Access envelope arrays
    t = result.t
    i_low = result.envelopes['I']['p5']
    i_high = result.envelopes['I']['p95']
    i_median = result.envelopes['I']['p50']

Comparing compartments::

    fig = result.plot(compartment='I', title="Infectious")
    fig = result.plot(compartment='R', title="Recovered")
    fig = result.plot(compartment='D', title="Deaths")
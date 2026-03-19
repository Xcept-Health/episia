scenarios Module
================

Multi-scenario runner for compartmental models.

This module provides tools to run multiple parameter scenarios through
a single model class and compare results.

Classes
-------

.. autoclass:: episia.models.scenarios.ScenarioRunner
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.scenarios.ScenarioResults
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __iter__, __len__, __repr__

Examples
--------

Comparing intervention strategies::

    from episia.models import SIRModel
    from episia.models.parameters import SIRParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner

    # Define scenarios
    baseline = SIRParameters(N=1e6, I0=10, beta=0.3, gamma=0.1)
    lockdown = SIRParameters(N=1e6, I0=10, beta=0.15, gamma=0.1)
    masks    = SIRParameters(N=1e6, I0=10, beta=0.2, gamma=0.1)
    vaccines = SIRParameters(N=1e6, I0=10, beta=0.25, gamma=0.15)  # Faster recovery

    scenarios = ScenarioSet([
        ("Baseline", baseline),
        ("Lockdown", lockdown),
        ("Masks only", masks),
        ("Vaccines", vaccines),
    ])

    # Run all scenarios
    runner = ScenarioRunner(SIRModel)
    results = runner.run(scenarios)

    # Compare metrics
    df = results.to_dataframe()
    print(df)

    # Visualize
    results.plot(compartment='I', title="Scenario Comparison: Infectious").show()

Comparing R₀ values::

    import numpy as np
    from episia.models import SIRModel
    from episia.models.parameters import SIRParameters, ScenarioSet
    from episia.models.scenarios import ScenarioRunner

    scenarios = ScenarioSet()
    for r0 in np.linspace(1.5, 4.0, 6):
        gamma = 0.1
        beta = r0 * gamma
        params = SIRParameters(N=1e6, I0=10, beta=beta, gamma=gamma)
        scenarios.add(f"R₀={r0:.1f}", params)

    results = ScenarioRunner(SIRModel).run(scenarios)
    results.plot(compartment='I').show()

Export results::

    # Metrics table
    df_metrics = results.to_dataframe()
    df_metrics.to_csv("scenario_comparison.csv")

    # Extract trajectories for each scenario
    for label, result in results:
        df_traj = result.to_dataframe()
        df_traj.to_csv(f"trajectory_{label}.csv")
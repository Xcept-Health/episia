parameters Module
=================

Parameter containers for compartmental models.

This module provides validated parameter classes for each model type,
with automatic calculation of derived quantities (R₀, CFR, etc.).

Classes
-------

.. autoclass:: episia.models.parameters.ModelParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.parameters.SIRParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.parameters.SEIRParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.parameters.SEIRDParameters
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: episia.models.parameters.ScenarioSet
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __iter__, __len__, __repr__

Examples
--------

SIR parameters::

    from episia.models.parameters import SIRParameters

    params = SIRParameters(
        N=1_000_000,      # Population
        I0=10,            # Initial infected
        beta=0.3,         # Transmission rate
        gamma=0.1,        # Recovery rate
        t_span=(0, 200)   # Simulation period
    )

    print(f"R₀: {params.r0:.2f}")
    print(f"Infectious period: {params.t_infectious:.1f} days")

SEIRD parameters with mortality::

    from episia.models.parameters import SEIRDParameters

    params = SEIRDParameters(
        N=1_000_000,
        I0=10,
        E0=50,
        beta=0.35,
        sigma=1/5.2,      # Incubation rate
        gamma=0.09,        # Recovery rate
        mu=0.01,           # Mortality rate
        t_span=(0, 365)
    )

    print(f"CFR: {params.cfr:.1%}")
    print(f"R₀: {params.r0:.2f}")

Scenario sets::

    from episia.models.parameters import SIRParameters, ScenarioSet

    baseline = SIRParameters(N=1e6, I0=10, beta=0.3, gamma=0.1)
    lockdown = SIRParameters(N=1e6, I0=10, beta=0.15, gamma=0.1)
    masks    = SIRParameters(N=1e6, I0=10, beta=0.2, gamma=0.1)

    scenarios = ScenarioSet([
        ("Baseline", baseline),
        ("Lockdown", lockdown),
        ("Masks only", masks),
    ])

    for label, params in scenarios:
        print(f"{label}: R₀={params.r0:.2f}")
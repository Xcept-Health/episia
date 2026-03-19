seir Module
===========

SEIR compartmental epidemic model with incubation period.

The SEIR model adds an **E**xposed (latent) compartment for diseases with
an incubation period where individuals are infected but not yet infectious.

Equations
---------

.. math::

    \\frac{dS}{dt} &= -\\frac{\\beta S I}{N} \\\\
    \\frac{dE}{dt} &=  \\frac{\\beta S I}{N} - \\sigma E \\\\
    \\frac{dI}{dt} &=  \\sigma E - \\gamma I \\\\
    \\frac{dR}{dt} &=  \\gamma I

where:
- :math:`\\beta` = transmission rate (day⁻¹)
- :math:`\\sigma` = progression rate E→I (day⁻¹)
- :math:`\\gamma` = recovery rate (day⁻¹)
- :math:`1/\\sigma` = mean incubation period
- :math:`1/\\gamma` = mean infectious period
- :math:`R_0 = \\beta / \\gamma`

Class
-----

.. autoclass:: episia.models.seir.SEIRModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Examples
--------

COVID-19 modeling::

    from episia.models import SEIRModel
    from episia.models.parameters import SEIRParameters

    params = SEIRParameters(
        N=1_000_000,
        I0=10,
        E0=50,               # Initial exposed
        beta=0.35,
        sigma=1/5.2,         # 5.2 days incubation
        gamma=1/14,          # 14 days infectious
        t_span=(0, 365)
    )

    model = SEIRModel(params)
    result = model.run()

    print(f"R₀: {params.r0:.2f}")
    print(f"Peak infected: {result.peak_infected:,.0f}")
    print(f"Peak exposed: {result.metadata['metrics']['peak_exposed']:,.0f}")

    result.plot().show()

Comparing with SIR::

    from episia.models import SIRModel, SEIRModel
    from episia.models.parameters import SIRParameters, SEIRParameters

    # SIR (no incubation)
    sir_params = SIRParameters(N=1e6, I0=10, beta=0.3, gamma=0.1)
    sir_result = SIRModel(sir_params).run()

    # SEIR (5 days incubation)
    seir_params = SEIRParameters(N=1e6, I0=10, E0=50, beta=0.3, 
                                  sigma=0.2, gamma=0.1)
    seir_result = SEIRModel(seir_params).run()

    print(f"SIR peak: {sir_result.peak_time:.0f} days")
    print(f"SEIR peak: {seir_result.peak_time:.0f} days")
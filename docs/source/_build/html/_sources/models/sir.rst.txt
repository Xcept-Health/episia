sir Module
==========

SIR compartmental epidemic model.

The classic SIR model divides the population into:
- **S**usceptible
- **I**nfectious
- **R**ecovered (immune)

Equations
---------

.. math::

    \\frac{dS}{dt} &= -\\frac{\\beta S I}{N} \\\\
    \\frac{dI}{dt} &=  \\frac{\\beta S I}{N} - \\gamma I \\\\
    \\frac{dR}{dt} &=  \\gamma I

where:
- :math:`\\beta` = transmission rate (day⁻¹)
- :math:`\\gamma` = recovery rate (day⁻¹)
- :math:`R_0 = \\beta / \\gamma`

Class
-----

.. autoclass:: episia.models.sir.SIRModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Examples
--------

Basic usage::

    from episia.models import SIRModel
    from episia.models.parameters import SIRParameters

    # COVID-19-like parameters
    params = SIRParameters(
        N=1_000_000,
        I0=10,
        beta=0.3,      # Transmission rate
        gamma=0.1,      # Recovery rate (10 days infectious period)
        t_span=(0, 200)
    )

    model = SIRModel(params)
    result = model.run()

    print(f"Peak infections: {result.peak_infected:,.0f}")
    print(f"Peak day: {result.peak_time:.0f}")
    print(f"Final size: {result.final_size:.1%}")

    result.plot().show()

Multiple runs with different R₀::

    import numpy as np
    from episia.models import SIRModel
    from episia.models.parameters import SIRParameters

    for r0 in [1.5, 2.5, 3.5]:
        gamma = 0.1
        beta = r0 * gamma
        params = SIRParameters(N=1e6, I0=10, beta=beta, gamma=gamma)
        result = SIRModel(params).run()
        print(f"R₀={r0:.1f}: peak={result.peak_infected:,.0f} at t={result.peak_time:.0f}")
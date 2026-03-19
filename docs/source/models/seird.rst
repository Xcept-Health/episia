seird Module
============

SEIRD compartmental epidemic model with mortality.

The SEIRD model adds a **D**eath compartment to account for disease-induced
mortality, essential for understanding outbreak severity.

Equations
---------

.. math::

    \\frac{dS}{dt} &= -\\frac{\\beta S I}{N} \\\\
    \\frac{dE}{dt} &=  \\frac{\\beta S I}{N} - \\sigma E \\\\
    \\frac{dI}{dt} &=  \\sigma E - (\\gamma + \\mu) I \\\\
    \\frac{dR}{dt} &=  \\gamma I \\\\
    \\frac{dD}{dt} &=  \\mu I

where:
- :math:`\\beta` = transmission rate (day⁻¹)
- :math:`\\sigma` = progression rate E→I (day⁻¹)
- :math:`\\gamma` = recovery rate (day⁻¹)
- :math:`\\mu` = mortality rate (day⁻¹)
- :math:`R_0 = \\beta / (\\gamma + \\mu)`
- :math:`CFR = \\mu / (\\gamma + \\mu)`

Class
-----

.. autoclass:: episia.models.seird.SEIRDModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Examples
--------

Mortality modeling::

    from episia.models import SEIRDModel
    from episia.models.parameters import SEIRDParameters

    params = SEIRDParameters(
        N=1_000_000,
        I0=10,
        E0=50,
        beta=0.35,
        sigma=1/5.2,
        gamma=0.09,    # 90% recover
        mu=0.01,       # 10% die
        t_span=(0, 365)
    )

    model = SEIRDModel(params)
    result = model.run()

    total_deaths = result.compartments['D'][-1]
    print(f"Total deaths: {total_deaths:,.0f}")
    print(f"CFR: {params.cfr:.1%}")
    print(f"Attack rate: {result.metadata['metrics']['attack_rate']:.1%}")

    result.plot().show()

Estimating hospital burden::

    result = SEIRDModel(params).run()
    
    # Peak infectious = peak hospital/ICU demand
    peak_inf = result.peak_infected
    peak_day = result.peak_time
    
    print(f"Peak hospital demand: {peak_inf:,.0f} patients at day {peak_day:.0f}")
    print(f"Cumulative deaths: {result.compartments['D'][-1]:,.0f}")
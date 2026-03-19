solver Module
=============

ODE solver wrapper for compartmental models.

This module wraps :func:`scipy.integrate.solve_ivp` with epidemic-specific
features: population conservation checks, stiff detection, and fallback
to Radau for stiff systems.

Functions
---------

.. autofunction:: episia.models.solver.solve_model
.. autofunction:: episia.models.solver.estimate_herd_immunity
.. autofunction:: episia.models.solver.doubling_time

Examples
--------

Basic solving::

    import numpy as np
    from episia.models.solver import solve_model

    def sir_derivatives(t, y):
        S, I, R = y
        N = 1000
        beta, gamma = 0.3, 0.1
        dS = -beta * S * I / N
        dI =  beta * S * I / N - gamma * I
        dR =  gamma * I
        return np.array([dS, dI, dR])

    y0 = [990, 10, 0]
    t, sol = solve_model(
        derivatives=sir_derivatives,
        y0=y0,
        t_span=(0, 200),
        t_eval=np.linspace(0, 200, 1000)
    )

Herd immunity::

    from episia.models.solver import estimate_herd_immunity

    for r0 in [1.5, 2.5, 3.5]:
        hit = estimate_herd_immunity(r0)
        print(f"R₀={r0:.1f}: need {hit:.1%} immune")

Doubling time::

    from episia.models.solver import doubling_time

    # Early epidemic growth
    t_double = doubling_time(beta=0.3, gamma=0.1)
    print(f"Cases double every {t_double:.1f} days")
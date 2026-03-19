base Module
===========

Abstract base class for all compartmental epidemic models.

This module defines the :class:`CompartmentalModel` abstract base class,
which provides a unified interface for all epidemic models in Episia.

Class
-----

.. autoclass:: episia.models.base.CompartmentalModel
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __repr__

Abstract Methods
----------------

Subclasses must implement:

- :meth:`~episia.models.base.CompartmentalModel.compartment_names`
- :meth:`~episia.models.base.CompartmentalModel._derivatives`
- :meth:`~episia.models.base.CompartmentalModel._initial_state`
- :meth:`~episia.models.base.CompartmentalModel._compute_metrics`

Examples
--------

Creating a custom model::

    from episia.models.base import CompartmentalModel
    from episia.models.parameters import ModelParameters
    import numpy as np

    class SISModel(CompartmentalModel):
        @property
        def compartment_names(self):
            return ["S", "I"]
        
        def _initial_state(self):
            p = self.parameters
            return np.array([p.S0, p.I0])
        
        def _derivatives(self, t, y):
            S, I = y
            N = self.parameters.N
            beta = self.parameters.beta
            gamma = self.parameters.gamma
            
            dS = -beta * S * I / N + gamma * I
            dI =  beta * S * I / N - gamma * I
            
            return np.array([dS, dI])
        
        def _compute_metrics(self, t, solution):
            S, I = solution
            return {
                "peak_infected": float(np.max(I)),
                "peak_time": float(t[np.argmax(I)]),
                "steady_state": float(I[-1])
            }

    params = ModelParameters(N=1000, I0=10, t_span=(0, 100))
    model = SISModel(params)
    result = model.run()
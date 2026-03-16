"""
models/seir.py - SEIR compartmental epidemic model.

    dS/dt = -β * S * I / N
    dE/dt =  β * S * I / N  - σ * E
    dI/dt =  σ * E          - γ * I
    dR/dt =  γ * I

The latent (exposed) compartment E accounts for the incubation period,
making SEIR more realistic than SIR for diseases like influenza or COVID-19.

References
----------
    Anderson & May (1991). Infectious Diseases of Humans. Oxford University Press.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from .base import CompartmentalModel
from .parameters import SEIRParameters


class SEIRModel(CompartmentalModel):
    """
    SEIR epidemic model with explicit incubation compartment.

    Args:
        parameters: SEIRParameters instance.

    Example::

        from episia.models import SEIRModel
        from episia.models.parameters import SEIRParameters

        params = SEIRParameters(
            N=1_000_000,
            I0=1,
            E0=10,
            beta=0.35,
            sigma=1/5.2,   # COVID-19-like incubation
            gamma=1/14,
            t_span=(0, 365),
        )
        result = SEIRModel(params).run()
        result.plot().show()
    """

    def __init__(self, parameters: SEIRParameters):
        if not isinstance(parameters, SEIRParameters):
            raise TypeError(
                f"Expected SEIRParameters, got {type(parameters).__name__}."
            )
        super().__init__(parameters)

    @property
    def compartment_names(self) -> List[str]:
        return ["S", "E", "I", "R"]

    def _initial_state(self) -> np.ndarray:
        p = self.parameters
        return np.array([p.S0, p.E0, p.I0, p.R0_init])

    def _derivatives(self, t: float, y: np.ndarray) -> np.ndarray:
        S, E, I, R = y
        N          = float(self.parameters.N)
        beta       = self.parameters.beta
        sigma      = self.parameters.sigma
        gamma      = self.parameters.gamma

        new_exposed  = beta * S * I / N
        new_infected = sigma * E

        dS = -new_exposed
        dE =  new_exposed   - new_infected
        dI =  new_infected  - gamma * I
        dR =  gamma * I

        return np.array([dS, dE, dI, dR])

    def _compute_metrics(
        self,
        t: np.ndarray,
        solution: np.ndarray,
    ) -> Dict[str, Any]:
        S, E, I, R = solution
        N = float(self.parameters.N)
        p = self.parameters

        peak_idx      = int(np.argmax(I))
        peak_infected = float(I[peak_idx])
        peak_time     = float(t[peak_idx])
        final_size    = float(R[-1]) / N

        # Peak exposed
        peak_exposed_idx = int(np.argmax(E))
        peak_exposed     = float(E[peak_exposed_idx])

        from .solver import estimate_herd_immunity
        hit = estimate_herd_immunity(p.r0)

        return {
            "r0":                       p.r0,
            "peak_infected":            peak_infected,
            "peak_time":                peak_time,
            "final_size":               final_size,
            "peak_exposed":             peak_exposed,
            "herd_immunity_threshold":  hit,
            "t_incubation":             p.t_incubation,
            "t_infectious":             p.t_infectious,
        }


__all__ = ["SEIRModel"]
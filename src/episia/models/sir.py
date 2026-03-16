"""
models/sir.py - SIR compartmental epidemic model.

    dS/dt = -β * S * I / N
    dI/dt =  β * S * I / N  - γ * I
    dR/dt =  γ * I

References
----------
    Kermack & McKendrick (1927). Proc. Royal Society A, 115, 700-721.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from .base import CompartmentalModel
from .parameters import SIRParameters


class SIRModel(CompartmentalModel):
    """
    SIR epidemic model.

    Args:
        parameters: SIRParameters instance.

    Example::

        from episia.models import SIRModel
        from episia.models.parameters import SIRParameters

        params = SIRParameters(
            N=1_000_000,
            I0=10,
            beta=0.3,
            gamma=0.1,
            t_span=(0, 200),
        )
        model = SIRModel(params)
        result = model.run()

        print(model.summary())
        result.plot().show()
    """

    def __init__(self, parameters: SIRParameters):
        if not isinstance(parameters, SIRParameters):
            raise TypeError(
                f"Expected SIRParameters, got {type(parameters).__name__}."
            )
        super().__init__(parameters)

    @property
    def compartment_names(self) -> List[str]:
        return ["S", "I", "R"]

    def _initial_state(self) -> np.ndarray:
        p = self.parameters
        return np.array([p.S0, p.I0, p.R0_init])

    def _derivatives(self, t: float, y: np.ndarray) -> np.ndarray:
        S, I, R = y
        N       = float(self.parameters.N)
        beta    = self.parameters.beta
        gamma   = self.parameters.gamma

        force_of_infection = beta * S * I / N

        dS = -force_of_infection
        dI =  force_of_infection - gamma * I
        dR =  gamma * I

        return np.array([dS, dI, dR])

    def _compute_metrics(
        self,
        t: np.ndarray,
        solution: np.ndarray,
    ) -> Dict[str, Any]:
        S, I, R = solution
        N = float(self.parameters.N)
        p = self.parameters

        # Peak
        peak_idx      = int(np.argmax(I))
        peak_infected = float(I[peak_idx])
        peak_time     = float(t[peak_idx])

        # Final size (fraction of population ever infected)
        final_size = float(R[-1]) / N

        # Herd immunity threshold
        from .solver import estimate_herd_immunity
        hit = estimate_herd_immunity(p.r0)

        return {
            "r0":            p.r0,
            "peak_infected": peak_infected,
            "peak_time":     peak_time,
            "final_size":    final_size,
            "herd_immunity_threshold": hit,
        }


__all__ = ["SIRModel"]
"""
models/seird.py - SEIRD compartmental epidemic model (with mortality).

    dS/dt = -β * S * I / N
    dE/dt =  β * S * I / N  - σ * E
    dI/dt =  σ * E          - γ * I  - μ * I
    dR/dt =  γ * I
    dD/dt =  μ * I

SEIRD extends SEIR with a disease-induced death compartment D.
μ is the per-capita mortality rate of infectious individuals (day⁻¹).

References
----------
    Giordano et al. (2020). Nature Medicine, 26, 855-860 (SIDARTHE model)
    Peng et al. (2020). arXiv:2002.06563
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from .base import CompartmentalModel
from .parameters import SEIRDParameters


class SEIRDModel(CompartmentalModel):
    """
    SEIRD epidemic model with disease-induced mortality.

    Args:
        parameters: SEIRDParameters instance.

    Example::

        from epitools.models import SEIRDModel
        from epitools.models.parameters import SEIRDParameters

        params = SEIRDParameters(
            N=1_000_000,
            I0=1,
            E0=5,
            beta=0.35,
            sigma=1/5.2,
            gamma=0.09,
            mu=0.01,       # ~10% CFR at peak load
            t_span=(0, 365),
        )
        result = SEIRDModel(params).run()
        print(f"Total deaths: {result.compartments['D'][-1]:,.0f}")
        result.plot().show()
    """

    def __init__(self, parameters: SEIRDParameters):
        if not isinstance(parameters, SEIRDParameters):
            raise TypeError(
                f"Expected SEIRDParameters, got {type(parameters).__name__}."
            )
        super().__init__(parameters)

    @property
    def compartment_names(self) -> List[str]:
        return ["S", "E", "I", "R", "D"]

    def _initial_state(self) -> np.ndarray:
        p = self.parameters
        return np.array([p.S0, p.E0, p.I0, p.R0_init, p.D0])

    def _derivatives(self, t: float, y: np.ndarray) -> np.ndarray:
        S, E, I, R, D = y
        N             = float(self.parameters.N)
        beta          = self.parameters.beta
        sigma         = self.parameters.sigma
        gamma         = self.parameters.gamma
        mu            = self.parameters.mu

        new_exposed  = beta * S * I / N
        new_infected = sigma * E

        dS = -new_exposed
        dE =  new_exposed   - new_infected
        dI =  new_infected  - (gamma + mu) * I
        dR =  gamma * I
        dD =  mu    * I

        return np.array([dS, dE, dI, dR, dD])

    def _compute_metrics(
        self,
        t: np.ndarray,
        solution: np.ndarray,
    ) -> Dict[str, Any]:
        S, E, I, R, D = solution
        N = float(self.parameters.N)
        p = self.parameters

        peak_idx      = int(np.argmax(I))
        peak_infected = float(I[peak_idx])
        peak_time     = float(t[peak_idx])
        final_size    = float(R[-1]) / N
        total_deaths  = float(D[-1])
        attack_rate   = (float(R[-1]) + total_deaths) / N

        from .solver import estimate_herd_immunity
        hit = estimate_herd_immunity(p.r0)

        # Daily deaths (finite difference)
        daily_deaths = np.diff(D)
        peak_death_idx  = int(np.argmax(daily_deaths))
        peak_death_time = float(t[peak_death_idx + 1])

        return {
            "r0":                       p.r0,
            "cfr":                      p.cfr,
            "peak_infected":            peak_infected,
            "peak_time":                peak_time,
            "final_size":               final_size,
            "total_deaths":             total_deaths,
            "attack_rate":              attack_rate,
            "peak_death_time":          peak_death_time,
            "herd_immunity_threshold":  hit,
            "t_incubation":             p.t_incubation,
            "t_infectious":             p.t_infectious,
        }

    def summary(self) -> Dict[str, Any]:
        """Extended summary including mortality metrics."""
        base = super().summary()
        if self._result is not None:
            metrics = self._result.metadata.get("metrics", {})
            base.update({
                "cfr":          self.parameters.cfr,
                "total_deaths": metrics.get("total_deaths"),
                "attack_rate":  metrics.get("attack_rate"),
            })
        return base


__all__ = ["SEIRDModel"]
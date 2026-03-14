"""
models/parameters.py - Parameter containers for compartmental models.

Classes
-------
    ModelParameters    base parameters shared by all models (N, t_span, I0)
    SIRParameters      beta, gamma
    SEIRParameters     beta, sigma, gamma
    SEIRDParameters    beta, sigma, gamma, mu
    ScenarioSet        collection of parameter sets for comparison

Validation is strict: nonsensical values (negative rates, N=0, R0<0)
raise ValueError immediately at construction time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class ModelParameters:
    """
    Base parameters shared by all compartmental models.

    Args:
        N:       Total population size.
        I0:      Initial number of infected individuals.
        E0:      Initial number of exposed (used by SEIR/SEIRD).
        R0_init: Initial recovered (default 0).
        D0:      Initial dead (used by SEIRD, default 0).
        t_span:  (t_start, t_end) in days.
        dt:      Output time step in days (informational only).
    """
    N:       int
    I0:      float
    E0:      float   = 0.0
    R0_init: float   = 0.0
    D0:      float   = 0.0
    t_span:  Tuple[float, float] = (0.0, 160.0)
    dt:      float   = 1.0

    def __post_init__(self) -> None:
        if self.N <= 0:
            raise ValueError(f"N must be > 0, got {self.N}.")
        if self.I0 < 0:
            raise ValueError(f"I0 must be >= 0, got {self.I0}.")
        if self.E0 < 0:
            raise ValueError(f"E0 must be >= 0, got {self.E0}.")
        if self.I0 + self.E0 + self.R0_init + self.D0 > self.N:
            raise ValueError(
                f"I0 + E0 + R0 + D0 ({self.I0+self.E0+self.R0_init+self.D0}) "
                f"exceeds N ({self.N})."
            )
        if self.t_span[0] >= self.t_span[1]:
            raise ValueError(
                f"t_span[0] must be < t_span[1], got {self.t_span}."
            )

    @property
    def S0(self) -> float:
        """Initial susceptibles derived from other compartments."""
        return float(self.N) - self.I0 - self.E0 - self.R0_init - self.D0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "N":       self.N,
            "I0":      self.I0,
            "E0":      self.E0,
            "R0_init": self.R0_init,
            "D0":      self.D0,
            "t_span":  list(self.t_span),
            "dt":      self.dt,
        }


# ---------------------------------------------------------------------------
# SIR
# ---------------------------------------------------------------------------

@dataclass
class SIRParameters(ModelParameters):
    """
    Parameters for the SIR model.

    Args:
        beta:  Transmission rate (day⁻¹).
        gamma: Recovery rate (day⁻¹).

    Derived:
        r0    = beta / gamma
        t_inf = 1 / gamma  (mean infectious period)
    """
    beta:  float = 0.3
    gamma: float = 0.1

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.beta <= 0:
            raise ValueError(f"beta must be > 0, got {self.beta}.")
        if self.gamma <= 0:
            raise ValueError(f"gamma must be > 0, got {self.gamma}.")

    @property
    def r0(self) -> float:
        """Basic reproduction number R₀ = β / γ."""
        return self.beta / self.gamma

    @property
    def t_infectious(self) -> float:
        """Mean infectious period in days."""
        return 1.0 / self.gamma

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"beta": self.beta, "gamma": self.gamma, "r0": self.r0})
        return d


# ---------------------------------------------------------------------------
# SEIR
# ---------------------------------------------------------------------------

@dataclass
class SEIRParameters(ModelParameters):
    """
    Parameters for the SEIR model.

    Args:
        beta:  Transmission rate (day⁻¹).
        sigma: Rate of progression from exposed to infectious (day⁻¹).
               1/sigma = mean incubation period.
        gamma: Recovery rate (day⁻¹).

    Derived:
        r0       = beta / gamma
        t_inc    = 1 / sigma
        t_inf    = 1 / gamma
    """
    beta:  float = 0.3
    sigma: float = 0.2
    gamma: float = 0.1

    def __post_init__(self) -> None:
        super().__post_init__()
        for name, val in [("beta", self.beta), ("sigma", self.sigma),
                          ("gamma", self.gamma)]:
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}.")

    @property
    def r0(self) -> float:
        """Basic reproduction number R₀ = β / γ."""
        return self.beta / self.gamma

    @property
    def t_incubation(self) -> float:
        """Mean incubation period in days."""
        return 1.0 / self.sigma

    @property
    def t_infectious(self) -> float:
        """Mean infectious period in days."""
        return 1.0 / self.gamma

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "beta":  self.beta,
            "sigma": self.sigma,
            "gamma": self.gamma,
            "r0":    self.r0,
        })
        return d


# ---------------------------------------------------------------------------
# SEIRD
# ---------------------------------------------------------------------------

@dataclass
class SEIRDParameters(ModelParameters):
    """
    Parameters for the SEIRD model (with death compartment).

    Args:
        beta:  Transmission rate (day⁻¹).
        sigma: Progression rate E→I (day⁻¹).
        gamma: Recovery rate (day⁻¹).
        mu:    Disease-induced mortality rate (day⁻¹).

    Derived:
        r0  = beta / (gamma + mu)
        cfr = mu / (gamma + mu)   (case fatality ratio)
    """
    beta:  float = 0.3
    sigma: float = 0.2
    gamma: float = 0.09
    mu:    float = 0.01

    def __post_init__(self) -> None:
        super().__post_init__()
        for name, val in [("beta", self.beta), ("sigma", self.sigma),
                          ("gamma", self.gamma)]:
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}.")
        if self.mu < 0:
            raise ValueError(f"mu must be >= 0, got {self.mu}.")

    @property
    def r0(self) -> float:
        """Basic reproduction number R₀ = β / (γ + μ)."""
        return self.beta / (self.gamma + self.mu)

    @property
    def cfr(self) -> float:
        """Case fatality ratio μ / (γ + μ)."""
        return self.mu / (self.gamma + self.mu)

    @property
    def t_incubation(self) -> float:
        return 1.0 / self.sigma

    @property
    def t_infectious(self) -> float:
        return 1.0 / (self.gamma + self.mu)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "beta":  self.beta,
            "sigma": self.sigma,
            "gamma": self.gamma,
            "mu":    self.mu,
            "r0":    self.r0,
            "cfr":   self.cfr,
        })
        return d


# ---------------------------------------------------------------------------
# ScenarioSet
# ---------------------------------------------------------------------------

@dataclass
class ScenarioSet:
    """
    Named collection of parameter sets for scenario comparison.

    Example::

        from epitools.models.parameters import SIRParameters, ScenarioSet

        baseline     = SIRParameters(N=1_000_000, I0=1, beta=0.3, gamma=0.1)
        intervention = SIRParameters(N=1_000_000, I0=1, beta=0.15, gamma=0.1)

        scenarios = ScenarioSet([
            ("Baseline",     baseline),
            ("50% reduction", intervention),
        ])
    """
    scenarios: List[Tuple[str, ModelParameters]] = field(default_factory=list)

    def add(self, label: str, params: ModelParameters) -> "ScenarioSet":
        """Append a scenario and return self for chaining."""
        self.scenarios.append((label, params))
        return self

    def __iter__(self):
        return iter(self.scenarios)

    def __len__(self) -> int:
        return len(self.scenarios)

    def labels(self) -> List[str]:
        return [label for label, _ in self.scenarios]

    def __repr__(self) -> str:
        return (
            f"ScenarioSet({len(self.scenarios)} scenarios: "
            f"{self.labels()})"
        )


__all__ = [
    "ModelParameters",
    "SIRParameters",
    "SEIRParameters",
    "SEIRDParameters",
    "ScenarioSet",
]
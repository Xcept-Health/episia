"""
models/base.py - Abstract base class for all compartmental epidemic models.

Every model (SIR, SEIR, SEIRD, custom) inherits from CompartmentalModel
and shares a unified interface:
    - run()       → ModelResult
    - plot()      → Figure (delegates to viz layer)
    - summary()   → dict of key epidemiological metrics
    - to_dataframe() → pandas DataFrame of trajectories
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class CompartmentalModel(ABC):
    """
    Abstract base class for compartmental epidemic models.

    Subclasses must implement:
        compartment_names   property listing compartment names (e.g. ['S','I','R'])
        _derivatives()      ODE right-hand side
        _initial_state()    initial conditions vector from parameters
        _compute_metrics()  derive R0, peak, final_size from solution

    The run() method is fully implemented here via _derivatives() and
    the shared solver in models.solver.
    """

    def __init__(self, parameters: "ModelParameters"):  # noqa: F821
        self.parameters = parameters
        self._result: Optional[Any] = None   # cached ModelResult after run()

    # abstract

    @property
    @abstractmethod
    def compartment_names(self) -> List[str]:
        """Ordered list of compartment names, e.g. ['S', 'I', 'R']."""
        ...

    @abstractmethod
    def _derivatives(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        ODE right-hand side.

        Args:
            t: Current time.
            y: State vector (same order as compartment_names).

        Returns:
            dy/dt vector.
        """
        ...

    @abstractmethod
    def _initial_state(self) -> np.ndarray:
        """
        Build initial conditions vector from self.parameters.

        Returns:
            1-D array with one value per compartment.
        """
        ...

    @abstractmethod
    def _compute_metrics(
        self,
        t: np.ndarray,
        solution: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Compute epidemiological metrics from solved trajectory.

        Args:
            t:        Time array.
            solution: (n_compartments × n_timepoints) array.

        Returns:
            Dict with at least: r0, peak_infected, peak_time, final_size.
        """
        ...

    # run

    def run(
        self,
        t_span: Optional[Tuple[float, float]] = None,
        t_eval: Optional[np.ndarray] = None,
        method: str = "RK45",
        rtol: float = 1e-6,
        atol: float = 1e-8,
    ) -> Any:
        """
        Solve the ODE system and return a ModelResult.

        Args:
            t_span:  (t_start, t_end). Defaults to parameters.t_span.
            t_eval:  Time points at which to store solution.
                     Defaults to np.linspace(t_start, t_end, 1000).
            method:  scipy solve_ivp integration method (default RK45).
            rtol:    Relative tolerance.
            atol:    Absolute tolerance.

        Returns:
            ModelResult (also cached as self._result).

        Raises:
            RuntimeError: If the solver fails to integrate.
        """
        from .solver import solve_model

        span  = t_span or self.parameters.t_span
        y0    = self._initial_state()

        if t_eval is None:
            n_pts = max(500, int((span[1] - span[0]) * 10))
            t_eval = np.linspace(span[0], span[1], n_pts)

        t, sol = solve_model(
            derivatives=self._derivatives,
            y0=y0,
            t_span=span,
            t_eval=t_eval,
            method=method,
            rtol=rtol,
            atol=atol,
        )

        metrics = self._compute_metrics(t, sol)
        self._result = self._build_result(t, sol, metrics)
        return self._result

    # result builder

    def _build_result(
        self,
        t: np.ndarray,
        sol: np.ndarray,
        metrics: Dict[str, Any],
    ) -> Any:
        """Assemble a ModelResult from solved trajectory and metrics."""
        from ..api.results import ModelResult

        compartments = {
            name: sol[i]
            for i, name in enumerate(self.compartment_names)
        }

        return ModelResult(
            model_type=self.__class__.__name__.replace("Model", ""),
            t=t,
            compartments=compartments,
            parameters=self.parameters.to_dict(),
            r0=metrics.get("r0"),
            peak_infected=metrics.get("peak_infected"),
            peak_time=metrics.get("peak_time"),
            final_size=metrics.get("final_size"),
        )

    # convenience

    def plot(self, backend: str = "plotly", **kwargs) -> Any:
        """
        Plot model trajectories.

        Runs the model first if not already run.

        Args:
            backend: 'plotly' or 'matplotlib'.
            **kwargs: Passed to PlotConfig.

        Returns:
            Figure object.
        """
        if self._result is None:
            self.run()
        return self._result.plot(backend=backend, **kwargs)

    def summary(self) -> Dict[str, Any]:
        """
        Return key epidemiological metrics.

        Runs the model first if not already run.
        """
        if self._result is None:
            self.run()
        return {
            "model":         self.__class__.__name__,
            "r0":            self._result.r0,
            "peak_infected": self._result.peak_infected,
            "peak_time":     self._result.peak_time,
            "final_size":    self._result.final_size,
            "parameters":    self.parameters.to_dict(),
        }

    def to_dataframe(self):
        """
        Return trajectory as pandas DataFrame.

        Runs the model first if not already run.
        """
        if self._result is None:
            self.run()
        return self._result.to_dataframe()

    def __repr__(self) -> str:
        status = "ready" if self._result is None else "solved"
        return (
            f"{self.__class__.__name__}("
            f"N={self.parameters.N:,}, "
            f"status={status})"
        )


__all__ = ["CompartmentalModel"]
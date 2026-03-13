"""
models/solver.py - ODE solver wrapper for compartmental models.

Wraps scipy.integrate.solve_ivp with:
    - Consistent error handling and diagnostic messages
    - Population conservation check
    - Adaptive dense output for smooth trajectories
    - Stiff-detection fallback (RK45 → Radau)

Public function: solve_model()
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp


def solve_model(
    derivatives: Callable[[float, np.ndarray], np.ndarray],
    y0: np.ndarray,
    t_span: Tuple[float, float],
    t_eval: Optional[np.ndarray] = None,
    method: str = "RK45",
    rtol: float = 1e-6,
    atol: float = 1e-8,
    max_step: float = np.inf,
    check_conservation: bool = True,
    conservation_tol: float = 1e-3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Solve an epidemic ODE system.

    Args:
        derivatives:         f(t, y) → dy/dt callable.
        y0:                  Initial state vector.
        t_span:              (t_start, t_end).
        t_eval:              Output time points. If None uses 1000 points.
        method:              scipy method: 'RK45' (default), 'RK23',
                             'DOP853', 'Radau', 'BDF', 'LSODA'.
        rtol:                Relative tolerance.
        atol:                Absolute tolerance.
        max_step:            Maximum step size (useful for stiff systems).
        check_conservation:  Raise if total population drifts > tol.
        conservation_tol:    Fractional tolerance for conservation check.

    Returns:
        (t, solution) where solution has shape (n_compartments, len(t)).

    Raises:
        RuntimeError: Solver failure or population not conserved.
    """
    if t_eval is None:
        n_pts = max(500, int((t_span[1] - t_span[0]) * 10))
        t_eval = np.linspace(t_span[0], t_span[1], n_pts)

    y0 = np.asarray(y0, dtype=float)
    N0 = y0.sum()

    sol = _integrate(derivatives, y0, t_span, t_eval, method, rtol, atol,
                     max_step)

    # Population conservation check
    if check_conservation and N0 > 0:
        drift = np.abs(sol.y.sum(axis=0) - N0).max() / N0
        if drift > conservation_tol:
            raise RuntimeError(
                f"Population not conserved: max drift = {drift:.2e} "
                f"(tolerance {conservation_tol:.2e}). "
                f"Try tighter rtol/atol or method='Radau'."
            )

    # Clip tiny negatives from numerical noise
    solution = np.clip(sol.y, 0.0, None)

    return sol.t, solution


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _integrate(
    f, y0, t_span, t_eval, method, rtol, atol, max_step,
):
    """Run solve_ivp with automatic stiff fallback."""
    sol = solve_ivp(
        f,
        t_span,
        y0,
        method=method,
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        max_step=max_step,
        dense_output=False,
    )

    if sol.success:
        return sol

    # Stiff fallback: try Radau if the non-stiff method failed
    if method not in ("Radau", "BDF", "LSODA"):
        sol_stiff = solve_ivp(
            f,
            t_span,
            y0,
            method="Radau",
            t_eval=t_eval,
            rtol=rtol,
            atol=atol,
            dense_output=False,
        )
        if sol_stiff.success:
            return sol_stiff

    raise RuntimeError(
        f"ODE solver failed (method={method}): {sol.message}. "
        f"Try method='Radau' or 'LSODA' for stiff systems."
    )


def estimate_herd_immunity(r0: float) -> float:
    """
    Herd immunity threshold: h = 1 - 1/R₀.

    Args:
        r0: Basic reproduction number.

    Returns:
        Fraction of population that needs immunity.

    Raises:
        ValueError: r0 <= 0.
    """
    if r0 <= 0:
        raise ValueError(f"R₀ must be > 0, got {r0}.")
    if r0 < 1.0:
        return 0.0
    return 1.0 - 1.0 / r0


def doubling_time(beta: float, gamma: float) -> float:
    """
    Early exponential doubling time T₂ = ln(2) / (β - γ).

    Valid only during the initial exponential growth phase (S ≈ N).

    Args:
        beta:  Transmission rate.
        gamma: Recovery rate.

    Returns:
        Doubling time in the same units as beta/gamma.

    Raises:
        ValueError: beta <= gamma (no growth).
    """
    r = beta - gamma
    if r <= 0:
        raise ValueError(
            f"beta ({beta}) must be > gamma ({gamma}) for exponential growth."
        )
    return float(np.log(2) / r)


__all__ = [
    "solve_model",
    "estimate_herd_immunity",
    "doubling_time",
]
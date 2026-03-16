"""
models/calibration.py - Parameter calibration for compartmental models.

Fits model parameters to observed incidence / death data using
scipy.optimize.minimize with bounds.

Public class: ModelCalibrator
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize, OptimizeResult


@dataclass
class CalibrationResult:
    """
    Result of a parameter calibration run.

    Attributes:
        parameters:   Best-fit parameter dict.
        loss:         Final loss value.
        success:      True if optimiser converged.
        message:      Optimiser message.
        n_iterations: Number of function evaluations.
        residuals:    Observed − predicted array.
    """
    parameters:   Dict[str, float]
    loss:         float
    success:      bool
    message:      str
    n_iterations: int
    residuals:    Optional[np.ndarray] = None

    def __repr__(self) -> str:
        status = "converged" if self.success else "failed"
        params = ", ".join(f"{k}={v:.4f}" for k, v in self.parameters.items())
        return (
            f"CalibrationResult({status}, loss={self.loss:.4f}, "
            f"params=[{params}])"
        )


class ModelCalibrator:
    """
    Fit a compartmental model to observed time-series data.

    Supports simultaneous fitting to multiple compartments
    (e.g. infected + deaths for SEIRD).

    Example::

        from episia.models.calibration import ModelCalibrator
        from episia.models.sir import SIRModel
        from episia.models.parameters import SIRParameters

        calibrator = ModelCalibrator(
            model_class=SIRModel,
            param_class=SIRParameters,
            fixed_params=dict(N=1_000_000, I0=1, t_span=(0, 60)),
            fit_params={
                "beta":  (0.05, 1.0),   # (lower_bound, upper_bound)
                "gamma": (0.01, 0.5),
            },
        )

        result = calibrator.fit(
            t_observed=days,
            observed={"I": infected_counts},
        )
        print(result)
    """

    def __init__(
        self,
        model_class,
        param_class,
        fixed_params: Dict[str, Any],
        fit_params: Dict[str, Tuple[float, float]],
        loss: str = "mse",
    ):
        """
        Args:
            model_class:   CompartmentalModel subclass (SIRModel, SEIRModel…).
            param_class:   Matching parameters class.
            fixed_params:  Parameters held constant during optimisation.
            fit_params:    Parameters to fit; values are (lower, upper) bounds.
            loss:          Loss function: 'mse', 'rmse', 'mae', 'poisson'.
        """
        self.model_class  = model_class
        self.param_class  = param_class
        self.fixed_params = fixed_params
        self.fit_params   = fit_params
        self.loss         = loss

    # public

    def fit(
        self,
        t_observed: np.ndarray,
        observed: Dict[str, np.ndarray],
        method: str = "L-BFGS-B",
        options: Optional[Dict] = None,
    ) -> CalibrationResult:
        """
        Fit model parameters to observed data.

        Args:
            t_observed:  Time points of observations (days).
            observed:    Dict mapping compartment name → array of observations.
                         E.g. {'I': infected_array} or {'I': ..., 'D': ...}.
            method:      scipy.optimize.minimize method (default L-BFGS-B).
            options:     Extra options for scipy.optimize.minimize.

        Returns:
            CalibrationResult with best-fit parameters and diagnostics.
        """
        t_obs = np.asarray(t_observed, dtype=float)

        param_names  = list(self.fit_params.keys())
        bounds       = [self.fit_params[k] for k in param_names]
        x0           = [np.mean(b) for b in bounds]  # start at midpoint

        result_cache: Dict = {}

        def objective(x: np.ndarray) -> float:
            trial_params = dict(zip(param_names, x))
            loss_val, residuals = self._evaluate(
                trial_params, t_obs, observed,
            )
            result_cache["last_residuals"] = residuals
            return loss_val

        opt_result: OptimizeResult = minimize(
            objective,
            x0=x0,
            bounds=bounds,
            method=method,
            options=options or {"maxiter": 500, "ftol": 1e-10},
        )

        best_params = dict(zip(param_names, opt_result.x))

        return CalibrationResult(
            parameters=best_params,
            loss=float(opt_result.fun),
            success=bool(opt_result.success),
            message=opt_result.message,
            n_iterations=int(opt_result.nfev),
            residuals=result_cache.get("last_residuals"),
        )

    def fit_and_apply(
        self,
        t_observed: np.ndarray,
        observed: Dict[str, np.ndarray],
        **fit_kwargs,
    ) -> Tuple[CalibrationResult, Any]:
        """
        Fit and immediately run the calibrated model.

        Returns:
            (CalibrationResult, ModelResult) tuple.
        """
        cal = self.fit(t_observed, observed, **fit_kwargs)
        model = self._build_model(cal.parameters)
        result = model.run()
        return cal, result

    # internal

    def _build_model(self, fit_params: Dict[str, float]):
        """Instantiate model with fixed + fitted parameters."""
        all_params = {**self.fixed_params, **fit_params}
        params = self.param_class(**all_params)
        return self.model_class(params)

    def _evaluate(
        self,
        fit_params: Dict[str, float],
        t_obs: np.ndarray,
        observed: Dict[str, np.ndarray],
    ) -> Tuple[float, np.ndarray]:
        """Run model, interpolate to t_obs, compute loss."""
        try:
            model  = self._build_model(fit_params)
            result = model.run()
        except Exception:
            # Return large penalty on solver failure
            total_n = sum(len(v) for v in observed.values())
            return 1e12, np.zeros(total_n)

        residuals_all = []
        total_loss    = 0.0

        for comp, obs in observed.items():
            predicted_full = result.compartments.get(comp)
            if predicted_full is None:
                total_loss += 1e12
                residuals_all.append(np.zeros(len(obs)))
                continue

            # Interpolate to observation times
            predicted = np.interp(t_obs, result.t, predicted_full)
            obs       = np.asarray(obs, dtype=float)
            res       = obs - predicted
            residuals_all.append(res)

            total_loss += self._compute_loss(obs, predicted)

        return total_loss, np.concatenate(residuals_all)

    def _compute_loss(
        self,
        obs: np.ndarray,
        pred: np.ndarray,
    ) -> float:
        """Compute scalar loss between observed and predicted."""
        eps = 1.0   # prevent log(0)
        if self.loss == "mse":
            return float(np.mean((obs - pred) ** 2))
        elif self.loss == "rmse":
            return float(np.sqrt(np.mean((obs - pred) ** 2)))
        elif self.loss == "mae":
            return float(np.mean(np.abs(obs - pred)))
        elif self.loss == "poisson":
            # Negative log-likelihood for Poisson counts
            pred_safe = np.clip(pred, eps, None)
            return float(np.sum(pred_safe - obs * np.log(pred_safe)))
        else:
            raise ValueError(
                f"Unknown loss '{self.loss}'. "
                f"Choose: 'mse', 'rmse', 'mae', 'poisson'."
            )


__all__ = ["ModelCalibrator", "CalibrationResult"]
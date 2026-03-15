"""
This module provides functions for fitting and interpreting
regression models commonly used in epidemiology, including
logistic regression for binary outcomes and Poisson regression
for count data.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, optimize
import pandas as pd
from sklearn.linear_model import LogisticRegression as SklearnLogistic
from sklearn.preprocessing import StandardScaler


class RegressionType(Enum):
    """Types of regression models."""
    LOGISTIC = "logistic"
    POISSON = "poisson"
    LINEAR = "linear"


class ModelSelection(Enum):
    """Model selection criteria."""
    AIC = "aic"
    BIC = "bic"
    LIKELIHOOD_RATIO = "likelihood_ratio"


@dataclass
class RegressionResult:
    """Result object for regression analysis."""
    coefficients: np.ndarray
    odds_ratios: np.ndarray
    ci_lower: np.ndarray
    ci_upper: np.ndarray
    p_values: np.ndarray
    variable_names: List[str]
    model_type: str
    n_observations: int
    log_likelihood: float
    aic: float
    bic: float
    convergence: bool
    iterations: int
    
    def __repr__(self) -> str:
        return f"RegressionResult({self.model_type}, n={self.n_observations}, AIC={self.aic:.1f})"
    
    def summary(self, decimal_places: int = 3) -> pd.DataFrame:
        """
        Create summary table of regression results.
        
        Args:
            decimal_places: Number of decimal places for display
            
        Returns:
            pandas DataFrame with results
        """
        data = []
        for i, var in enumerate(self.variable_names):
            if self.model_type == "logistic":
                measure = self.odds_ratios[i]
                ci_str = f"{self.ci_lower[i]:.{decimal_places}f}-{self.ci_upper[i]:.{decimal_places}f}"
            else:
                measure = self.coefficients[i]
                ci_str = f"{self.ci_lower[i]:.{decimal_places}f}-{self.ci_upper[i]:.{decimal_places}f}"
            
            data.append({
                "Variable": var,
                "Coefficient": round(self.coefficients[i], decimal_places),
                "OR" if self.model_type == "logistic" else "Coefficient": round(measure, decimal_places),
                "95% CI": ci_str,
                "p-value": f"{self.p_values[i]:.{decimal_places}f}" if self.p_values[i] >= 0.001 else "<0.001"
            })
        
        df = pd.DataFrame(data)
        
        # Add model statistics
        stats_df = pd.DataFrame([{
            "Variable": "Model Statistics",
            "Coefficient": f"n={self.n_observations}",
            "OR" if self.model_type == "logistic" else "Coefficient": f"LL={self.log_likelihood:.1f}",
            "95% CI": f"AIC={self.aic:.1f}",
            "p-value": f"BIC={self.bic:.1f}"
        }])
        
        return pd.concat([df, stats_df], ignore_index=True)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities or expected counts.
        
        Args:
            X: Design matrix (including intercept if needed)
            
        Returns:
            Predicted values
        """
        if self.model_type == "logistic":
            linear_predictor = X @ self.coefficients
            return 1 / (1 + np.exp(-linear_predictor))
        else:
            return np.exp(X @ self.coefficients)


def logistic_regression(
    X: np.ndarray,
    y: np.ndarray,
    variable_names: Optional[List[str]] = None,
    add_intercept: bool = True,
    method: str = "irls",
    max_iter: int = 100,
    tol: float = 1e-6
) -> RegressionResult:
    """
    Fit logistic regression model for binary outcomes.
    
    Args:
        X: Design matrix (n_samples, n_features)
        y: Binary outcome (0 or 1)
        variable_names: Names of predictor variables
        add_intercept: Whether to add intercept term
        method: Fitting method ('irls' or 'newton')
        max_iter: Maximum iterations
        tol: Convergence tolerance
        
    Returns:
        RegressionResult object
        
    Example:
        >>> X = np.array([[1, 25], [1, 30], [1, 35], [0, 40]])
        >>> y = np.array([1, 1, 0, 0])
        >>> result = logistic_regression(X, y, ['exposed', 'age'])
    """
    # Input validation
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    
    if X.shape[0] != len(y):
        raise ValueError("X and y must have same number of observations")
    
    if not np.all(np.isin(y, [0, 1])):
        raise ValueError("y must contain only 0 and 1 values")
    
    # Add intercept if requested
    if add_intercept:
        X = np.column_stack([np.ones(X.shape[0]), X])
        if variable_names is not None:
            variable_names = ["Intercept"] + variable_names
        else:
            variable_names = ["Intercept"] + [f"X{i}" for i in range(X.shape[1] - 1)]
    elif variable_names is None:
        variable_names = [f"X{i}" for i in range(X.shape[1])]
    
    n_obs, n_vars = X.shape
    
    # Initialize coefficients
    beta = np.zeros(n_vars)
    
    if method == "irls":
        beta, converged, iterations, log_likelihood = _irls_logistic(X, y, beta, max_iter, tol)
    elif method == "newton":
        beta, converged, iterations, log_likelihood = _newton_logistic(X, y, beta, max_iter, tol)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Calculate standard errors and confidence intervals
    se, p_values = _logistic_standard_errors(X, y, beta)
    
    # Odds ratios and confidence intervals
    odds_ratios = np.exp(beta)
    z = stats.norm.ppf(0.975)
    ci_lower = np.exp(beta - z * se)
    ci_upper = np.exp(beta + z * se)
    
    # Model fit statistics
    aic = -2 * log_likelihood + 2 * n_vars
    bic = -2 * log_likelihood + n_vars * np.log(n_obs)
    
    return RegressionResult(
        coefficients=beta,
        odds_ratios=odds_ratios,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_values=p_values,
        variable_names=variable_names,
        model_type="logistic",
        n_observations=n_obs,
        log_likelihood=log_likelihood,
        aic=aic,
        bic=bic,
        convergence=converged,
        iterations=iterations
    )


def _irls_logistic(
    X: np.ndarray,
    y: np.ndarray,
    beta_init: np.ndarray,
    max_iter: int,
    tol: float
) -> Tuple[np.ndarray, bool, int, float]:
    """
    Iteratively Reweighted Least Squares for logistic regression.
    """
    beta = beta_init.copy()
    n_obs = X.shape[0]
    
    for iteration in range(max_iter):
        # Current predictions
        linear_predictor = X @ beta
        p = 1 / (1 + np.exp(-linear_predictor))
        
        # Avoid extreme probabilities
        p = np.clip(p, 1e-10, 1 - 1e-10)
        
        # Weights and working response
        W = np.diag(p * (1 - p))
        z = linear_predictor + (y - p) / (p * (1 - p))
        
        # Update beta
        XTW = X.T @ W
        XTWX = XTW @ X
        XTWz = XTW @ z
        
        try:
            beta_new = np.linalg.solve(XTWX, XTWz)
        except np.linalg.LinAlgError:
            # Use pseudo-inverse if singular
            beta_new = np.linalg.pinv(XTWX) @ XTWz
        
        # Check convergence
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        
        beta = beta_new
    
    # Calculate log-likelihood
    linear_predictor = X @ beta
    p = 1 / (1 + np.exp(-linear_predictor))
    p = np.clip(p, 1e-10, 1 - 1e-10)
    log_likelihood = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    
    converged = iteration < max_iter - 1
    
    return beta, converged, iteration + 1, log_likelihood


def _newton_logistic(
    X: np.ndarray,
    y: np.ndarray,
    beta_init: np.ndarray,
    max_iter: int,
    tol: float
) -> Tuple[np.ndarray, bool, int, float]:
    """
    Newton-Raphson method for logistic regression.
    """
    beta = beta_init.copy()
    
    for iteration in range(max_iter):
        linear_predictor = X @ beta
        p = 1 / (1 + np.exp(-linear_predictor))
        p = np.clip(p, 1e-10, 1 - 1e-10)
        
        # Gradient
        gradient = X.T @ (y - p)
        
        # Hessian
        W = np.diag(p * (1 - p))
        hessian = -X.T @ W @ X
        
        try:
            # Newton update
            delta = np.linalg.solve(-hessian, gradient)
        except np.linalg.LinAlgError:
            # Use gradient descent if Hessian is singular
            delta = 0.01 * gradient
        
        beta_new = beta - delta
        
        # Check convergence
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        
        beta = beta_new
    
    # Log-likelihood
    linear_predictor = X @ beta
    p = 1 / (1 + np.exp(-linear_predictor))
    p = np.clip(p, 1e-10, 1 - 1e-10)
    log_likelihood = np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    
    converged = iteration < max_iter - 1
    
    return beta, converged, iteration + 1, log_likelihood


def _logistic_standard_errors(
    X: np.ndarray,
    y: np.ndarray,
    beta: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate standard errors and p-values for logistic regression.
    """
    n_obs = X.shape[0]
    
    # Predictions at final beta
    linear_predictor = X @ beta
    p = 1 / (1 + np.exp(-linear_predictor))
    p = np.clip(p, 1e-10, 1 - 1e-10)
    
    # Fisher information matrix
    W = np.diag(p * (1 - p))
    information = X.T @ W @ X
    
    try:
        # Variance-covariance matrix
        vcov = np.linalg.inv(information)
    except np.linalg.LinAlgError:
        # Use pseudo-inverse if singular
        vcov = np.linalg.pinv(information)
    
    # Standard errors
    se = np.sqrt(np.diag(vcov))
    
    # Wald test statistics
    z_scores = beta / se
    
    # Two-sided p-values
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z_scores)))
    
    return se, p_values


def poisson_regression(
    X: np.ndarray,
    y: np.ndarray,
    offset: Optional[np.ndarray] = None,
    variable_names: Optional[List[str]] = None,
    add_intercept: bool = True,
    max_iter: int = 100,
    tol: float = 1e-6
) -> RegressionResult:
    """
    Fit Poisson regression model for count data.
    
    Args:
        X: Design matrix
        y: Count outcome (non-negative integers)
        offset: Offset term (e.g., log(person-time))
        variable_names: Names of predictor variables
        add_intercept: Whether to add intercept term
        max_iter: Maximum iterations
        tol: Convergence tolerance
        
    Returns:
        RegressionResult object
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    
    if np.any(y < 0):
        raise ValueError("y must contain non-negative values")
    
    if offset is not None:
        offset = np.asarray(offset, dtype=float)
        if len(offset) != len(y):
            raise ValueError("offset must have same length as y")
    else:
        offset = np.zeros(len(y))
    
    # Add intercept
    if add_intercept:
        X = np.column_stack([np.ones(X.shape[0]), X])
        if variable_names is not None:
            variable_names = ["Intercept"] + variable_names
        else:
            variable_names = ["Intercept"] + [f"X{i}" for i in range(X.shape[1] - 1)]
    elif variable_names is None:
        variable_names = [f"X{i}" for i in range(X.shape[1])]
    
    n_obs, n_vars = X.shape
    
    # Initialize coefficients
    beta = np.zeros(n_vars)
    
    # Fit using Newton-Raphson
    for iteration in range(max_iter):
        linear_predictor = X @ beta + offset
        mu = np.exp(linear_predictor)
        
        # Avoid extreme values
        mu = np.clip(mu, 1e-10, 1e10)
        
        # Gradient
        gradient = X.T @ (y - mu)
        
        # Hessian
        W = np.diag(mu)
        hessian = -X.T @ W @ X
        
        try:
            delta = np.linalg.solve(-hessian, gradient)
        except np.linalg.LinAlgError:
            delta = 0.01 * gradient
        
        beta_new = beta - delta
        
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        
        beta = beta_new
    
    # Calculate log-likelihood
    linear_predictor = X @ beta + offset
    mu = np.exp(linear_predictor)
    mu = np.clip(mu, 1e-10, 1e10)
    log_likelihood = np.sum(y * np.log(mu) - mu - np.log(np.math.factorial(y.astype(int))))
    
    # Standard errors
    W = np.diag(mu)
    information = X.T @ W @ X
    
    try:
        vcov = np.linalg.inv(information)
    except np.linalg.LinAlgError:
        vcov = np.linalg.pinv(information)
    
    se = np.sqrt(np.diag(vcov))
    
    # Rate ratios and confidence intervals
    rate_ratios = np.exp(beta)
    z = stats.norm.ppf(0.975)
    ci_lower = np.exp(beta - z * se)
    ci_upper = np.exp(beta + z * se)
    
    # P-values
    z_scores = beta / se
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z_scores)))
    
    # Model statistics
    aic = -2 * log_likelihood + 2 * n_vars
    bic = -2 * log_likelihood + n_vars * np.log(n_obs)
    
    return RegressionResult(
        coefficients=beta,
        odds_ratios=rate_ratios,  # Actually rate ratios for Poisson
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_values=p_values,
        variable_names=variable_names,
        model_type="poisson",
        n_observations=n_obs,
        log_likelihood=log_likelihood,
        aic=aic,
        bic=bic,
        convergence=iteration < max_iter - 1,
        iterations=iteration + 1
    )


def likelihood_ratio_test(
    model_full: RegressionResult,
    model_reduced: RegressionResult
) -> Dict[str, float]:
    """
    Perform likelihood ratio test between nested models.
    
    Args:
        model_full: Full model (more parameters)
        model_reduced: Reduced model (fewer parameters)
        
    Returns:
        Dictionary with test statistics
    """
    if model_full.model_type != model_reduced.model_type:
        raise ValueError("Models must be of same type")
    
    if model_full.n_observations != model_reduced.n_observations:
        raise ValueError("Models must be fit on same data")
    
    # Test statistic
    lr_stat = 2 * (model_full.log_likelihood - model_reduced.log_likelihood)
    
    # Degrees of freedom
    df = len(model_full.coefficients) - len(model_reduced.coefficients)
    
    # P-value
    p_value = 1 - stats.chi2.cdf(lr_stat, df) if df > 0 else 1.0
    
    return {
        "lr_statistic": lr_stat,
        "df": df,
        "p_value": p_value,
        "full_aic": model_full.aic,
        "reduced_aic": model_reduced.aic,
        "full_bic": model_full.bic,
        "reduced_bic": model_reduced.bic
    }


def hosmer_lemeshow_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_groups: int = 10
) -> Dict[str, float]:
    """
    Hosmer-Lemeshow goodness-of-fit test for logistic regression.
    
    Args:
        y_true: True binary outcomes
        y_pred: Predicted probabilities
        n_groups: Number of groups to form
        
    Returns:
        Dictionary with test statistics
    """
    # Sort by predicted probability
    sort_idx = np.argsort(y_pred)
    y_true_sorted = y_true[sort_idx]
    y_pred_sorted = y_pred[sort_idx]
    
    # Create groups
    group_size = len(y_true) // n_groups
    chi2 = 0.0
    
    observed_counts = []
    expected_counts = []
    
    for g in range(n_groups):
        start = g * group_size
        end = start + group_size if g < n_groups - 1 else len(y_true)
        
        group_true = y_true_sorted[start:end]
        group_pred = y_pred_sorted[start:end]
        
        observed = np.sum(group_true)
        expected = np.sum(group_pred)
        
        if expected > 0:
            chi2 += (observed - expected)**2 / (expected * (1 - expected / len(group_true)))
        
        observed_counts.append(observed)
        expected_counts.append(expected)
    
    df = n_groups - 2
    p_value = 1 - stats.chi2.cdf(chi2, df) if df > 0 else 1.0
    
    return {
        "chi2": chi2,
        "df": df,
        "p_value": p_value,
        "n_groups": n_groups,
        "observed": observed_counts,
        "expected": expected_counts
    }


def calculate_vif(X: np.ndarray) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors for multicollinearity detection.
    
    Args:
        X: Design matrix (without intercept)
        
    Returns:
        Dictionary with VIF for each variable
    """
    X = np.asarray(X, dtype=float)
    n_vars = X.shape[1]
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    vif = {}
    for i in range(1, n_vars + 1):  # Skip intercept
        # Regress variable i on all other variables
        y = X_with_intercept[:, i]
        X_other = np.delete(X_with_intercept, i, axis=1)
        
        # Solve normal equations
        try:
            beta = np.linalg.solve(X_other.T @ X_other, X_other.T @ y)
            y_pred = X_other @ beta
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        except np.linalg.LinAlgError:
            r2 = 0
        
        vif_value = 1 / (1 - r2) if r2 < 1 else float('inf')
        vif[f"X{i}"] = vif_value
    
    return vif


def stepwise_selection(
    X: np.ndarray,
    y: np.ndarray,
    model_type: RegressionType = RegressionType.LOGISTIC,
    direction: str = "both",
    criterion: ModelSelection = ModelSelection.AIC,
    max_vars: Optional[int] = None
) -> Dict:
    """
    Perform stepwise variable selection.
    
    Args:
        X: Design matrix
        y: Outcome
        model_type: Type of regression model
        direction: 'forward', 'backward', or 'both'
        criterion: Selection criterion
        max_vars: Maximum number of variables to include
        
    Returns:
        Dictionary with selected model and steps
    """
    n_obs, n_vars = X.shape
    if max_vars is None:
        max_vars = min(n_vars, n_obs // 10)  # Rule of thumb
    
    # Variable indices
    current_vars = set()
    candidate_vars = set(range(n_vars))
    
    steps = []
    best_model = None
    best_criterion = float('inf')
    
    if direction in ["forward", "both"]:
        # Forward selection
        while len(current_vars) < max_vars and candidate_vars:
            best_var = None
            best_score = float('inf')
            
            for var in candidate_vars:
                test_vars = list(current_vars | {var})
                X_test = X[:, test_vars]
                
                if model_type == RegressionType.LOGISTIC:
                    model = logistic_regression(X_test, y, add_intercept=True)
                else:
                    model = poisson_regression(X_test, y, add_intercept=True)
                
                score = model.aic if criterion == ModelSelection.AIC else model.bic
                
                if score < best_score:
                    best_score = score
                    best_var = var
            
            if best_var is not None:
                current_vars.add(best_var)
                candidate_vars.remove(best_var)
                
                steps.append({
                    "step": len(steps) + 1,
                    "action": "add",
                    "variable": best_var,
                    "criterion": best_score
                })
                
                if best_score < best_criterion:
                    best_criterion = best_score
                    best_model = model
    
    if direction in ["backward", "both"] and len(current_vars) > 1:
        # Backward elimination (simplified)
        pass
    
    return {
        "selected_variables": list(current_vars),
        "best_model": best_model,
        "steps": steps,
        "final_criterion": best_criterion,
        "direction": direction
    }


def roc_auc_from_logistic(
    model: RegressionResult,
    X: np.ndarray,
    y: np.ndarray
) -> float:
    """
    Calculate ROC AUC from logistic regression model.
    
    Args:
        model: Fitted logistic regression model
        X: Design matrix (with intercept if model has it)
        y: True outcomes
        
    Returns:
        AUC value
    """
    # Predict probabilities
    y_pred = model.predict(X)
    
    # Calculate AUC (simplified)
    from sklearn.metrics import roc_auc_score
    try:
        auc = roc_auc_score(y, y_pred)
    except:
        # Fallback calculation
        n_pos = np.sum(y == 1)
        n_neg = np.sum(y == 0)
        
        if n_pos == 0 or n_neg == 0:
            return 0.5
        
        # Manual AUC calculation
        pos_pred = y_pred[y == 1]
        neg_pred = y_pred[y == 0]
        
        auc = 0
        for p in pos_pred:
            auc += np.sum(neg_pred < p) + 0.5 * np.sum(neg_pred == p)
        
        auc /= (n_pos * n_neg)
    
    return auc


def interaction_term(
    X1: np.ndarray,
    X2: np.ndarray,
    center: bool = True
) -> np.ndarray:
    """
    Create interaction term for regression.
    
    Args:
        X1: First variable
        X2: Second variable
        center: Whether to center variables before multiplying
        
    Returns:
        Interaction term
    """
    X1 = np.asarray(X1, dtype=float)
    X2 = np.asarray(X2, dtype=float)
    
    if center:
        X1_centered = X1 - np.mean(X1)
        X2_centered = X2 - np.mean(X2)
        interaction = X1_centered * X2_centered
    else:
        interaction = X1 * X2
    
    return interaction


#  MODULE EXPORTS 

__all__ = [
    'RegressionType',
    'ModelSelection',
    'RegressionResult',
    'logistic_regression',
    'poisson_regression',
    'likelihood_ratio_test',
    'hosmer_lemeshow_test',
    'calculate_vif',
    'stepwise_selection',
    'roc_auc_from_logistic',
    'interaction_term'
]
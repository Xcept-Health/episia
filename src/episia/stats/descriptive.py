"""
descriptive.py - Descriptive statistics for epidemiological data.

This module provides functions for calculating confidence intervals
for proportions, means, and other descriptive statistics commonly
used in epidemiological analysis.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import warnings


class CI_Method(Enum):
    """Methods for calculating confidence intervals."""
    WALD = "wald"
    WILSON = "wilson"
    AGRESTI_COULL = "agresti_coull"
    JEFFREYS = "jeffreys"
    CLOPPER_PEARSON = "clopper_pearson"
    DELTA = "delta"


@dataclass
class ProportionResult:
    """Rich result object for proportion calculations."""
    proportion: float
    ci_lower: float
    ci_upper: float
    sample_size: int
    numerator: int
    denominator: int
    method: str
    
    def __repr__(self) -> str:
        return f"Proportion: {self.proportion:.4f} ({self.ci_lower:.4f}-{self.ci_upper:.4f})"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "measure": "proportion",
            "proportion": self.proportion,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "sample_size": self.sample_size,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "method": self.method
        }


@dataclass
class MeanResult:
    """Rich result object for mean calculations."""
    mean: float
    ci_lower: float
    ci_upper: float
    sample_size: int
    std_dev: float
    method: str
    
    def __repr__(self) -> str:
        return f"Mean: {self.mean:.4f} ({self.ci_lower:.4f}-{self.ci_upper:.4f})"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "measure": "mean",
            "mean": self.mean,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "sample_size": self.sample_size,
            "std_dev": self.std_dev,
            "method": self.method
        }


def proportion_ci(
    numerator: int = None,
    denominator: int = None,
    method: CI_Method = CI_Method.WILSON,
    confidence: float = 0.95,
    *,
    k: int = None,
    n: int = None,
    **kwargs
) -> ProportionResult:
    """Wrapper accepting both proportion_ci(45, 200) and proportion_ci(k=45, n=200)."""
    # Resolve aliases k/n → numerator/denominator
    if numerator is None and k is not None:
        numerator = k
    if denominator is None and n is not None:
        denominator = n
    if numerator is None or denominator is None:
        raise TypeError(
            "proportion_ci() requires numerator and denominator. "
            "Use proportion_ci(45, 200) or proportion_ci(k=45, n=200)."
        )
    return _proportion_ci_impl(numerator, denominator, method, confidence, **kwargs)


def _proportion_ci_impl(
    numerator: int,
    denominator: int,
    method = CI_Method.WILSON,
    confidence: float = 0.95,
    **kwargs
) -> ProportionResult:
    # Accept string method names e.g. method="wilson"
    if isinstance(method, str):
        try:
            method = CI_Method(method.lower())
        except ValueError:
            method = CI_Method.WILSON
    """
    Calculate proportion with confidence interval.
    
    Args:
        numerator: Number of events/cases
        denominator: Total sample size
        method: Method for CI calculation (default: Wilson)
        confidence: Confidence level (default: 0.95)
        **kwargs: Additional method-specific parameters
        
    Returns:
        ProportionResult object
        
    Raises:
        ValueError: If denominator <= 0 or numerator < 0
        ValueError: If numerator > denominator
        
    Example:
        >>> result = proportion_ci(45, 100)
        >>> print(result.proportion)
        0.45
    """
    # Input validation
    if denominator <= 0:
        raise ValueError("Denominator must be positive")
    if numerator < 0:
        raise ValueError("Numerator must be non-negative")
    if numerator > denominator:
        raise ValueError("Numerator cannot exceed denominator")
    
    p = numerator / denominator if denominator > 0 else 0.0
    
    # Select CI calculation method
    if method == CI_Method.WALD:
        ci_lower, ci_upper = _wald_ci(p, denominator, confidence, **kwargs)
    elif method == CI_Method.WILSON:
        ci_lower, ci_upper = _wilson_ci(numerator, denominator, confidence, **kwargs)
    elif method == CI_Method.AGRESTI_COULL:
        ci_lower, ci_upper = _agresti_coull_ci(numerator, denominator, confidence, **kwargs)
    elif method == CI_Method.JEFFREYS:
        ci_lower, ci_upper = _jeffreys_ci(numerator, denominator, confidence, **kwargs)
    elif method == CI_Method.CLOPPER_PEARSON:
        ci_lower, ci_upper = _clopper_pearson_ci(numerator, denominator, confidence, **kwargs)
    else:
        # Default to Wilson
        ci_lower, ci_upper = _wilson_ci(numerator, denominator, confidence, **kwargs)
    
    return ProportionResult(
        proportion=p,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        sample_size=denominator,
        numerator=numerator,
        denominator=denominator,
        method=method.value
    )


def mean_ci(
    data: np.ndarray,
    confidence: float = 0.95,
    method: str = "t_distribution",
    population_std: Optional[float] = None
) -> MeanResult:
    """
    Calculate mean with confidence interval.
    
    Args:
        data: Array-like numeric data
        confidence: Confidence level (default: 0.95)
        method: 't_distribution' (small samples) or 'normal' (large samples)
        population_std: Known population standard deviation (optional)
        
    Returns:
        MeanResult object
        
    Example:
        >>> data = np.array([1.2, 1.5, 1.8, 2.1, 1.9])
        >>> result = mean_ci(data)
        >>> print(result.mean)
    """
    # Convert to numpy array if needed
    if not isinstance(data, np.ndarray):
        data = np.array(data)
    
    # Remove NaN values
    data = data[~np.isnan(data)]
    
    n = len(data)
    if n == 0:
        raise ValueError("Data array is empty or contains only NaN values")
    
    mean = np.mean(data)
    std = np.std(data, ddof=1)  # Sample standard deviation
    
    if population_std is not None:
        # Use known population standard deviation
        se = population_std / np.sqrt(n)
        z = _z_score(confidence)
        margin = z * se
    elif method == "t_distribution" and n < 30:
        # Use t-distribution for small samples
        from scipy import stats
        t = stats.t.ppf(1 - (1 - confidence) / 2, df=n-1)
        se = std / np.sqrt(n)
        margin = t * se
    else:
        # Use normal approximation for large samples
        z = _z_score(confidence)
        se = std / np.sqrt(n)
        margin = z * se
    
    ci_lower = mean - margin
    ci_upper = mean + margin
    
    return MeanResult(
        mean=mean,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        sample_size=n,
        std_dev=std,
        method=method
    )


def incidence_rate(
    cases: int,
    person_time: float,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Calculate incidence rate (cases per person-time) with CI.
    
    Args:
        cases: Number of incident cases
        person_time: Total person-time at risk
        confidence: Confidence level
        
    Returns:
        Dictionary with rate, CI, and other statistics
        
    Example:
        >>> result = incidence_rate(10, 1000)
        >>> print(result['rate'])
        0.01  # 10 cases per 1000 person-time units
    """
    if person_time <= 0:
        raise ValueError("Person-time must be positive")
    
    rate = cases / person_time
    
    # Byar's approximation (good for cases >= 10)
    if cases >= 10:
        z = _z_score(confidence)
        ci_lower = cases * (1 - 1/(9*cases) - z/(3*np.sqrt(cases)))**3 / person_time
        ci_upper = (cases + 1) * (1 - 1/(9*(cases+1)) + z/(3*np.sqrt(cases+1)))**3 / person_time
    else:
        # Exact Poisson CI for small numbers
        from scipy import stats
        ci_lower = stats.chi2.ppf((1-confidence)/2, 2*cases) / (2*person_time)
        ci_upper = stats.chi2.ppf(1-(1-confidence)/2, 2*(cases+1)) / (2*person_time)
    
    return {
        "measure": "incidence_rate",
        "rate": rate,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "cases": cases,
        "person_time": person_time,
        "confidence": confidence
    }


def attack_rate(
    cases: int,
    population: int,
    confidence: float = 0.95
) -> ProportionResult:
    """
    Calculate attack rate (cumulative incidence) with CI.
    
    Args:
        cases: Number of cases
        population: Population at risk
        confidence: Confidence level
        
    Returns:
        ProportionResult object
    """
    return proportion_ci(cases, population, confidence=confidence)


def prevalence(
    cases: int,
    population: int,
    confidence: float = 0.95
) -> ProportionResult:
    """
    Calculate point prevalence with CI.
    
    Args:
        cases: Number of prevalent cases
        population: Total population
        confidence: Confidence level
        
    Returns:
        ProportionResult object
    """
    return proportion_ci(cases, population, confidence=confidence)


#  CONFIDENCE INTERVAL METHODS 

def _wald_ci(
    p: float,
    n: int,
    confidence: float,
    **kwargs
) -> Tuple[float, float]:
    """
    Wald confidence interval for a proportion.
    
    Appropriate for large samples (n > 30) with p not near 0 or 1.
    """
    if n == 0:
        return 0.0, 0.0
    
    z = _z_score(confidence)
    se = np.sqrt(p * (1 - p) / n)
    margin = z * se
    
    ci_lower = max(0, p - margin)
    ci_upper = min(1, p + margin)
    
    return ci_lower, ci_upper


def _wilson_ci(
    numerator: int,
    denominator: int,
    confidence: float,
    **kwargs
) -> Tuple[float, float]:
    """
    Wilson score confidence interval.
    
    Recommended for all sample sizes, especially when p is near 0 or 1.
    """
    if denominator == 0:
        return 0.0, 0.0
    
    n = denominator
    x = numerator
    p = x / n
    z = _z_score(confidence)
    z2 = z**2
    
    center = (x + z2/2) / (n + z2)
    margin = z * np.sqrt((p*(1-p) + z2/(4*n)) / n) / (1 + z2/n)
    
    ci_lower = max(0, center - margin)
    ci_upper = min(1, center + margin)
    
    return ci_lower, ci_upper


def _agresti_coull_ci(
    numerator: int,
    denominator: int,
    confidence: float,
    **kwargs
) -> Tuple[float, float]:
    """
    Agresti-Coull confidence interval (adjusted Wald).
    
    Good alternative to Wilson, simpler calculation.
    """
    if denominator == 0:
        return 0.0, 0.0
    
    n = denominator
    x = numerator
    z = _z_score(confidence)
    z2 = z**2
    
    # Add z^2/2 successes and z^2/2 failures
    n_adj = n + z2
    p_adj = (x + z2/2) / n_adj
    
    se_adj = np.sqrt(p_adj * (1 - p_adj) / n_adj)
    margin = z * se_adj
    
    ci_lower = max(0, p_adj - margin)
    ci_upper = min(1, p_adj + margin)
    
    return ci_lower, ci_upper


def _jeffreys_ci(
    numerator: int,
    denominator: int,
    confidence: float,
    **kwargs
) -> Tuple[float, float]:
    """
    Jeffreys Bayesian confidence interval.
    
    Good properties for all sample sizes.
    """
    if denominator == 0:
        return 0.0, 0.0
    
    from scipy import stats
    
    x = numerator
    n = denominator
    
    # Beta distribution parameters
    alpha = x + 0.5
    beta = n - x + 0.5
    
    ci_lower = stats.beta.ppf((1-confidence)/2, alpha, beta)
    ci_upper = stats.beta.ppf(1-(1-confidence)/2, alpha, beta)
    
    return ci_lower, ci_upper


def _clopper_pearson_ci(
    numerator: int,
    denominator: int,
    confidence: float,
    **kwargs
) -> Tuple[float, float]:
    """
    Clopper-Pearson exact binomial confidence interval.
    
    Conservative - guaranteed coverage at least (1-alpha).
    """
    if denominator == 0:
        return 0.0, 0.0
    
    from scipy import stats
    
    x = numerator
    n = denominator
    
    if x == 0:
        ci_lower = 0.0
        ci_upper = 1 - (confidence/2)**(1/n)
    elif x == n:
        ci_lower = (confidence/2)**(1/n)
        ci_upper = 1.0
    else:
        ci_lower = stats.beta.ppf((1-confidence)/2, x, n-x+1)
        ci_upper = stats.beta.ppf(1-(1-confidence)/2, x+1, n-x)
    
    return ci_lower, ci_upper


def _z_score(confidence: float) -> float:
    """Get z-score for given confidence level."""
    from scipy import stats
    alpha = 1 - confidence
    return stats.norm.ppf(1 - alpha/2)


def _check_sample_size(
    n: int,
    p: Optional[float] = None,
    min_size: int = 5
) -> bool:
    """
    Check if sample size is adequate for normal approximation.
    
    Returns:
        True if n*p and n*(1-p) are both >= min_size
    """
    if p is None:
        return n >= 30  # Rule of thumb for means
    
    return n * p >= min_size and n * (1 - p) >= min_size


#  ADDITIONAL DESCRIPTIVE FUNCTIONS 

def median_ci(
    data: np.ndarray,
    confidence: float = 0.95,
    method: str = "exact"
) -> Dict[str, float]:
    """
    Calculate median with confidence interval.
    
    Args:
        data: Array-like numeric data
        confidence: Confidence level
        method: 'exact' or 'normal_approximation'
        
    Returns:
        Dictionary with median and CI
    """
    data = np.array(data)
    data = data[~np.isnan(data)]
    n = len(data)
    
    if n == 0:
        raise ValueError("Data array is empty")
    
    median = np.median(data)
    
    if method == "exact":
        # Binomial-based exact CI for median
        from scipy import stats
        
        # Order statistics indices
        r = int(np.floor((n/2) - stats.norm.ppf(1-(1-confidence)/2) * np.sqrt(n)/2))
        s = int(np.ceil(1 + (n/2) + stats.norm.ppf(1-(1-confidence)/2) * np.sqrt(n)/2))
        
        # Adjust for array indices (0-based)
        r = max(0, r - 1)
        s = min(n-1, s - 1)
        
        sorted_data = np.sort(data)
        ci_lower = sorted_data[r]
        ci_upper = sorted_data[s]
    else:
        # Normal approximation
        se = 1.253 * np.std(data, ddof=1) / np.sqrt(n)
        z = _z_score(confidence)
        margin = z * se
        
        ci_lower = median - margin
        ci_upper = median + margin
    
    return {
        "measure": "median",
        "median": median,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "sample_size": n,
        "method": method
    }


def interquartile_range(
    data: np.ndarray,
    return_quartiles: bool = False
) -> Union[float, Dict[str, float]]:
    """
    Calculate interquartile range (IQR).
    
    Args:
        data: Array-like numeric data
        return_quartiles: If True, returns Q1, Q3, and IQR
        
    Returns:
        IQR value or dictionary with quartiles
    """
    data = np.array(data)
    data = data[~np.isnan(data)]
    
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    if return_quartiles:
        return {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_fence": q1 - 1.5 * iqr,
            "upper_fence": q3 + 1.5 * iqr
        }
    
    return iqr


#  MODULE EXPORTS 

__all__ = [
    'CI_Method',
    'ProportionResult',
    'MeanResult',
    'proportion_ci',
    'mean_ci',
    'incidence_rate',
    'attack_rate',
    'prevalence',
    'median_ci',
    'interquartile_range'
]
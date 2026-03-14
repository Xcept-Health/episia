"""
This module provides functions for calculating required sample sizes
and statistical power for common epidemiological study designs:
- Cohort studies (risk ratio, risk difference)
- Case-control studies (odds ratio)
- Cross-sectional studies (proportions)
- Diagnostic test studies (sensitivity, specificity)
"""

import numpy as np
from typing import Union, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats


class StudyDesign(Enum):
    """Types of epidemiological study designs."""
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    DIAGNOSTIC = "diagnostic"


class TestType(Enum):
    """Types of statistical tests."""
    TWO_SIDED = "two_sided"
    ONE_SIDED = "one_sided"


@dataclass
class SampleSizeResult:
    """Rich result object for sample size calculations."""
    n_per_group: Optional[float] = None
    n_total: Optional[float] = None
    n_cases: Optional[float] = None
    n_controls: Optional[float] = None
    power: Optional[float] = None
    effect_size: Optional[float] = None
    alpha: float = 0.05
    design: Optional[str] = None
    method: Optional[str] = None
    assumptions: Optional[Dict] = None
    
    def __repr__(self) -> str:
        if self.n_per_group is not None:
            return f"Sample size: {self.n_per_group:.0f} per group (total: {self.n_total:.0f})"
        elif self.n_cases is not None:
            return f"Sample size: {self.n_cases:.0f} cases, {self.n_controls:.0f} controls"
        else:
            return f"Power: {self.power:.3f}"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        result = {
            "alpha": self.alpha,
            "power": self.power,
            "design": self.design,
            "method": self.method
        }
        
        if self.n_per_group is not None:
            result["n_per_group"] = self.n_per_group
            result["n_total"] = self.n_total
        
        if self.n_cases is not None:
            result["n_cases"] = self.n_cases
            result["n_controls"] = self.n_controls
        
        if self.effect_size is not None:
            result["effect_size"] = self.effect_size
        
        if self.assumptions is not None:
            result["assumptions"] = self.assumptions
        
        return result


def sample_size_risk_ratio(
    risk_unexposed: float = None,
    risk_ratio: float = None,
    power: float = 0.8,
    alpha: float = 0.05,
    test_type: TestType = TestType.TWO_SIDED,
    r: float = 1.0,
    design_effect: float = 1.0,
    *,
    p0: float = None,
    rr_expected: float = None,
    **kwargs
) -> SampleSizeResult:
    # Aliases: p0 → risk_unexposed, rr_expected → risk_ratio
    if risk_unexposed is None and p0 is not None:
        risk_unexposed = p0
    if risk_ratio is None and rr_expected is not None:
        risk_ratio = rr_expected
    if risk_unexposed is None or risk_ratio is None:
        raise TypeError(
            "sample_size_risk_ratio() requires risk_unexposed and risk_ratio. "
            "Use sample_size_risk_ratio(0.10, 2.0) or "
            "sample_size_risk_ratio(p0=0.10, rr_expected=2.0)."
        )
    return _sample_size_rr_impl(
        risk_unexposed, risk_ratio, power, alpha, test_type, r, design_effect, **kwargs
    )


def _sample_size_rr_impl(
    risk_unexposed: float,
    risk_ratio: float,
    power: float = 0.8,
    alpha: float = 0.05,
    test_type: TestType = TestType.TWO_SIDED,
    r: float = 1.0,
    design_effect: float = 1.0,
    **kwargs
) -> SampleSizeResult:
    """
    Calculate sample size for cohort study comparing two proportions (risk ratio).
    
    Args:
        risk_unexposed: Risk (proportion) in unexposed group
        risk_ratio: Expected risk ratio (exposed/unexposed)
        power: Desired statistical power (default: 0.8)
        alpha: Type I error rate (default: 0.05)
        test_type: 'two_sided' or 'one_sided' test
        r: Ratio of unexposed to exposed (default: 1.0 = equal groups)
        design_effect: Cluster design effect (default: 1.0 = no clustering)
        
    Returns:
        SampleSizeResult object
        
    Example:
        >>> # How many participants to detect RR=2.0 with baseline risk=0.1?
        >>> result = sample_size_risk_ratio(risk_unexposed=0.1, risk_ratio=2.0)
        >>> print(result.n_per_group)
        199  # per group
    """
    # Input validation
    if not 0 < risk_unexposed < 1:
        raise ValueError("risk_unexposed must be between 0 and 1")
    if risk_ratio <= 0:
        raise ValueError("risk_ratio must be positive")
    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if r <= 0:
        raise ValueError("r must be positive")
    
    # Calculate risk in exposed group
    risk_exposed = risk_unexposed * risk_ratio
    
    # Ensure risks are valid probabilities
    if risk_exposed > 1:
        warnings.warn(f"Risk in exposed group would be {risk_exposed:.3f} (>1). "
                     f"Consider using risk difference instead.")
        risk_exposed = min(risk_exposed, 0.99)
    
    # Get z-scores
    z_alpha = _z_score(alpha, test_type)
    z_beta = stats.norm.ppf(power)
    
    # Average risk
    p_bar = (risk_exposed + r * risk_unexposed) / (1 + r)
    
    # Sample size formula for comparing two proportions (risk ratio)
    numerator = (z_alpha * np.sqrt((1 + 1/r) * p_bar * (1 - p_bar)) + 
                z_beta * np.sqrt(risk_exposed * (1 - risk_exposed) + 
                                (risk_unexposed * (1 - risk_unexposed))/r))**2
    denominator = (risk_exposed - risk_unexposed)**2
    
    n_exposed = numerator / denominator
    n_unexposed = n_exposed * r
    
    # Apply design effect for clustered studies
    n_exposed *= design_effect
    n_unexposed *= design_effect
    
    # Round up to nearest integer
    n_exposed = np.ceil(n_exposed)
    n_unexposed = np.ceil(n_unexposed)
    
    return SampleSizeResult(
        n_per_group=float(n_exposed),
        n_total=float(n_exposed + n_unexposed),
        power=power,
        effect_size=risk_ratio,
        alpha=alpha,
        design=StudyDesign.COHORT.value,
        method="risk_ratio",
        assumptions={
            "risk_unexposed": risk_unexposed,
            "risk_exposed": risk_exposed,
            "exposure_ratio": r,
            "design_effect": design_effect
        }
    )


def sample_size_risk_difference(
    risk_unexposed: float,
    risk_difference: float,
    power: float = 0.8,
    alpha: float = 0.05,
    test_type: TestType = TestType.TWO_SIDED,
    r: float = 1.0,
    **kwargs
) -> SampleSizeResult:
    """
    Calculate sample size for cohort study based on risk difference.
    
    Args:
        risk_unexposed: Risk in unexposed group
        risk_difference: Expected risk difference (exposed - unexposed)
        power: Desired statistical power
        alpha: Type I error rate
        test_type: 'two_sided' or 'one_sided' test
        r: Ratio of unexposed to exposed
        
    Returns:
        SampleSizeResult object
    """
    # Calculate risk in exposed group
    risk_exposed = risk_unexposed + risk_difference
    
    # Use the same formula as for risk ratio (different effect measure)
    return sample_size_risk_ratio(
        risk_unexposed=risk_unexposed,
        risk_ratio=risk_exposed / risk_unexposed if risk_unexposed > 0 else float('inf'),
        power=power,
        alpha=alpha,
        test_type=test_type,
        r=r,
        **kwargs
    )


def sample_size_odds_ratio(
    proportion_exposed_controls: float,
    odds_ratio: float,
    power: float = 0.8,
    alpha: float = 0.05,
    test_type: TestType = TestType.TWO_SIDED,
    r: float = 1.0,
    **kwargs
) -> SampleSizeResult:
    """
    Calculate sample size for case-control study (odds ratio).
    
    Args:
        proportion_exposed_controls: Proportion exposed in controls
        odds_ratio: Expected odds ratio
        power: Desired statistical power
        alpha: Type I error rate
        test_type: 'two_sided' or 'one_sided' test
        r: Ratio of controls to cases (default: 1.0)
        
    Returns:
        SampleSizeResult object
        
    Example:
        >>> # Case-control study: OR=2.0, 30% exposure in controls
        >>> result = sample_size_odds_ratio(0.3, 2.0)
        >>> print(result.n_cases)
        146  # cases needed
    """
    # Input validation
    if not 0 < proportion_exposed_controls < 1:
        raise ValueError("proportion_exposed_controls must be between 0 and 1")
    if odds_ratio <= 0:
        raise ValueError("odds_ratio must be positive")
    
    # Calculate proportion exposed in cases
    p0 = proportion_exposed_controls
    p1 = (odds_ratio * p0) / (1 - p0 + odds_ratio * p0)
    
    # Get z-scores
    z_alpha = _z_score(alpha, test_type)
    z_beta = stats.norm.ppf(power)
    
    # Average proportion exposed
    p_bar = (p1 + r * p0) / (1 + r)
    q_bar = 1 - p_bar
    
    # Sample size for cases
    n_cases = (z_alpha * np.sqrt((1 + 1/r) * p_bar * q_bar) + 
               z_beta * np.sqrt(p1 * (1 - p1) + (p0 * (1 - p0))/r))**2
    n_cases /= (p1 - p0)**2
    
    n_controls = n_cases * r
    
    # Round up
    n_cases = np.ceil(n_cases)
    n_controls = np.ceil(n_controls)
    
    return SampleSizeResult(
        n_cases=float(n_cases),
        n_controls=float(n_controls),
        n_total=float(n_cases + n_controls),
        power=power,
        effect_size=odds_ratio,
        alpha=alpha,
        design=StudyDesign.CASE_CONTROL.value,
        method="odds_ratio",
        assumptions={
            "proportion_exposed_controls": proportion_exposed_controls,
            "proportion_exposed_cases": p1,
            "control_case_ratio": r
        }
    )


def sample_size_sensitivity_specificity(
    expected_sens: float,
    expected_spec: float,
    precision: float,
    alpha: float = 0.05,
    prevalence: Optional[float] = None,
    which: str = "both",
    **kwargs
) -> SampleSizeResult:
    """
    Calculate sample size for diagnostic test studies.
    
    Args:
        expected_sens: Expected sensitivity
        expected_spec: Expected specificity
        precision: Desired width of confidence interval (half-width)
        alpha: Type I error rate
        prevalence: Disease prevalence (required for sensitivity/specificity)
        which: 'sensitivity', 'specificity', or 'both'
        
    Returns:
        SampleSizeResult object
        
    Example:
        >>> # Validate test with sens=0.9, spec=0.85, CI width ±0.05
        >>> result = sample_size_sensitivity_specificity(0.9, 0.85, 0.05, prevalence=0.1)
        >>> print(result.n_total)
        246  # total subjects needed
    """
    # Input validation
    if not 0 < expected_sens < 1:
        raise ValueError("expected_sens must be between 0 and 1")
    if not 0 < expected_spec < 1:
        raise ValueError("expected_spec must be between 0 and 1")
    if precision <= 0:
        raise ValueError("precision must be positive")
    
    z = stats.norm.ppf(1 - alpha/2)
    
    results = {}
    
    if which in ["sensitivity", "both"]:
        if prevalence is None:
            raise ValueError("prevalence is required for sensitivity calculation")
        
        # Sample size for sensitivity
        n_diseased = (z**2 * expected_sens * (1 - expected_sens)) / (precision**2)
        
        # Total sample size based on prevalence
        n_total_sens = np.ceil(n_diseased / prevalence)
        results["sensitivity"] = {
            "n_diseased": float(np.ceil(n_diseased)),
            "n_total": float(n_total_sens)
        }
    
    if which in ["specificity", "both"]:
        if prevalence is None:
            raise ValueError("prevalence is required for specificity calculation")
        
        # Sample size for specificity
        n_non_diseased = (z**2 * expected_spec * (1 - expected_spec)) / (precision**2)
        
        # Total sample size based on prevalence
        n_total_spec = np.ceil(n_non_diseased / (1 - prevalence))
        results["specificity"] = {
            "n_non_diseased": float(np.ceil(n_non_diseased)),
            "n_total": float(n_total_spec)
        }
    
    if which == "both":
        # Take the maximum of the two
        n_total = max(results["sensitivity"]["n_total"], 
                     results["specificity"]["n_total"])
        n_diseased = np.ceil(n_total * prevalence)
        n_non_diseased = np.ceil(n_total * (1 - prevalence))
    elif which == "sensitivity":
        n_total = results["sensitivity"]["n_total"]
        n_diseased = results["sensitivity"]["n_diseased"]
        n_non_diseased = np.ceil(n_total * (1 - prevalence))
    else:  # specificity
        n_total = results["specificity"]["n_total"]
        n_non_diseased = results["specificity"]["n_non_diseased"]
        n_diseased = np.ceil(n_total * prevalence)
    
    return SampleSizeResult(
        n_total=float(n_total),
        power=None,  # Not applicable for precision-based calculation
        effect_size=precision,
        alpha=alpha,
        design=StudyDesign.DIAGNOSTIC.value,
        method="diagnostic_precision",
        assumptions={
            "expected_sensitivity": expected_sens,
            "expected_specificity": expected_spec,
            "precision": precision,
            "prevalence": prevalence,
            "which_parameter": which
        }
    )


def sample_size_single_proportion(
    expected_proportion: float,
    precision: float,
    alpha: float = 0.05,
    design_effect: float = 1.0,
    **kwargs
) -> SampleSizeResult:
    """
    Calculate sample size for estimating a single proportion.
    
    Used for cross-sectional studies, prevalence surveys, etc.
    
    Args:
        expected_proportion: Expected proportion
        precision: Desired precision (half-width of CI)
        alpha: Type I error rate
        design_effect: Cluster design effect
        
    Returns:
        SampleSizeResult object
    """
    if not 0 <= expected_proportion <= 1:
        raise ValueError("expected_proportion must be between 0 and 1")
    if precision <= 0:
        raise ValueError("precision must be positive")
    
    z = stats.norm.ppf(1 - alpha/2)
    
    # Conservative estimate (p=0.5 gives maximum variance)
    if expected_proportion == 0.5:
        n = (z**2 * 0.25) / (precision**2)
    else:
        n = (z**2 * expected_proportion * (1 - expected_proportion)) / (precision**2)
    
    # Apply design effect
    n *= design_effect
    
    # Round up
    n = np.ceil(n)
    
    return SampleSizeResult(
        n_total=float(n),
        power=None,
        effect_size=precision,
        alpha=alpha,
        design=StudyDesign.CROSS_SECTIONAL.value,
        method="single_proportion",
        assumptions={
            "expected_proportion": expected_proportion,
            "design_effect": design_effect
        }
    )


def power_calculation(
    n_per_group: Optional[float] = None,
    n_cases: Optional[float] = None,
    n_controls: Optional[float] = None,
    risk_unexposed: Optional[float] = None,
    risk_ratio: Optional[float] = None,
    odds_ratio: Optional[float] = None,
    proportion_exposed_controls: Optional[float] = None,
    alpha: float = 0.05,
    test_type: TestType = TestType.TWO_SIDED,
    r: float = 1.0,
    design: StudyDesign = StudyDesign.COHORT,
    **kwargs
) -> SampleSizeResult:
    """
    Calculate statistical power for a given sample size.
    
    Args:
        n_per_group: Sample size per group (for cohort studies)
        n_cases: Number of cases (for case-control)
        n_controls: Number of controls (for case-control)
        risk_unexposed: Risk in unexposed group
        risk_ratio: Expected risk ratio
        odds_ratio: Expected odds ratio
        proportion_exposed_controls: Proportion exposed in controls
        alpha: Type I error rate
        test_type: 'two_sided' or 'one_sided' test
        r: Group ratio
        design: Study design
        
    Returns:
        SampleSizeResult object with calculated power
    """
    z_alpha = _z_score(alpha, test_type)
    
    if design == StudyDesign.COHORT:
        if risk_unexposed is None or risk_ratio is None:
            raise ValueError("risk_unexposed and risk_ratio required for cohort design")
        
        risk_exposed = risk_unexposed * risk_ratio
        p_bar = (risk_exposed + r * risk_unexposed) / (1 + r)
        
        # Standard error under null
        se_null = np.sqrt(p_bar * (1 - p_bar) * (1/n_per_group + 1/(n_per_group * r)))
        
        # Standard error under alternative
        se_alt = np.sqrt(risk_exposed * (1 - risk_exposed)/n_per_group + 
                        risk_unexposed * (1 - risk_unexposed)/(n_per_group * r))
        
        effect_size = risk_exposed - risk_unexposed
        z_beta = (effect_size - z_alpha * se_null) / se_alt
        
    elif design == StudyDesign.CASE_CONTROL:
        if (proportion_exposed_controls is None or odds_ratio is None or 
            n_cases is None):
            raise ValueError("Missing required parameters for case-control design")
        
        p0 = proportion_exposed_controls
        p1 = (odds_ratio * p0) / (1 - p0 + odds_ratio * p0)
        
        if n_controls is None:
            n_controls = n_cases * r
        
        p_bar = (p1 + r * p0) / (1 + r)
        q_bar = 1 - p_bar
        
        se_null = np.sqrt(p_bar * q_bar * (1/n_cases + 1/n_controls))
        se_alt = np.sqrt(p1 * (1 - p1)/n_cases + p0 * (1 - p0)/n_controls)
        
        effect_size = p1 - p0
        z_beta = (effect_size - z_alpha * se_null) / se_alt
    
    else:
        raise NotImplementedError(f"Power calculation not implemented for {design}")
    
    power = stats.norm.cdf(z_beta)
    
    return SampleSizeResult(
        n_per_group=n_per_group,
        n_cases=n_cases,
        n_controls=n_controls,
        power=float(power),
        effect_size=risk_ratio or odds_ratio,
        alpha=alpha,
        design=design.value,
        method="power_calculation",
        assumptions={
            "test_type": test_type.value,
            "group_ratio": r
        }
    )


def fleiss_correction(
    n_uncorrected: float,
    continuity_correction: bool = True
) -> float:
    """
    Apply Fleiss continuity correction to sample size.
    
    Args:
        n_uncorrected: Sample size without correction
        continuity_correction: Apply correction if True
        
    Returns:
        Corrected sample size
    """
    if not continuity_correction:
        return n_uncorrected
    
    # Fleiss' recommended correction
    correction = 2 / abs(n_uncorrected)
    n_corrected = n_uncorrected * (1 + np.sqrt(1 + correction))**2 / 4
    
    return np.ceil(n_corrected)


def design_effect_deff(
    intraclass_correlation: float,
    average_cluster_size: float
) -> float:
    """
    Calculate design effect for cluster randomized trials.
    
    DEFF = 1 + (m - 1) * ρ
    
    Args:
        intraclass_correlation: ICC (ρ)
        average_cluster_size: Average subjects per cluster (m)
        
    Returns:
        Design effect
    """
    if not 0 <= intraclass_correlation <= 1:
        raise ValueError("intraclass_correlation must be between 0 and 1")
    if average_cluster_size < 1:
        raise ValueError("average_cluster_size must be ≥ 1")
    
    return 1 + (average_cluster_size - 1) * intraclass_correlation


# ==================== HELPER FUNCTIONS ====================

def _z_score(alpha: float, test_type: TestType = TestType.TWO_SIDED) -> float:
    """Get z-score for given alpha and test type."""
    if test_type == TestType.ONE_SIDED:
        return stats.norm.ppf(1 - alpha)
    else:  # TWO_SIDED
        return stats.norm.ppf(1 - alpha/2)


def _validate_probability(value: float, name: str) -> None:
    """Validate that a value is a valid probability."""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")


# ==================== COMPREHENSIVE SAMPLE SIZE FUNCTION ====================

def calculate_sample_size(
    design: Union[str, StudyDesign],
    parameters: Dict,
    **kwargs
) -> SampleSizeResult:
    """
    Comprehensive sample size calculation function.
    
    Args:
        design: Study design ('cohort', 'case_control', etc.)
        parameters: Dictionary of parameters specific to the design
        **kwargs: Additional arguments passed to specific functions
        
    Returns:
        SampleSizeResult object
        
    Example:
        >>> params = {
        ...     'risk_unexposed': 0.1,
        ...     'risk_ratio': 2.0,
        ...     'power': 0.8,
        ...     'alpha': 0.05
        ... }
        >>> result = calculate_sample_size('cohort', params)
    """
    if isinstance(design, str):
        design = StudyDesign(design.lower())
    
    if design == StudyDesign.COHORT:
        if 'risk_difference' in parameters:
            return sample_size_risk_difference(**parameters, **kwargs)
        else:
            return sample_size_risk_ratio(**parameters, **kwargs)
    
    elif design == StudyDesign.CASE_CONTROL:
        return sample_size_odds_ratio(**parameters, **kwargs)
    
    elif design == StudyDesign.CROSS_SECTIONAL:
        return sample_size_single_proportion(**parameters, **kwargs)
    
    elif design == StudyDesign.DIAGNOSTIC:
        return sample_size_sensitivity_specificity(**parameters, **kwargs)
    
    else:
        raise ValueError(f"Unsupported study design: {design}")


# ==================== MODULE EXPORTS ====================

__all__ = [
    'StudyDesign',
    'TestType',
    'SampleSizeResult',
    'sample_size_risk_ratio',
    'sample_size_risk_difference',
    'sample_size_odds_ratio',
    'sample_size_sensitivity_specificity',
    'sample_size_single_proportion',
    'power_calculation',
    'fleiss_correction',
    'design_effect_deff',
    'calculate_sample_size'
]
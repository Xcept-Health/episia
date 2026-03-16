"""
This module provides functions for stratified analysis, including
Mantel-Haenszel methods for adjusting for confounding variables
and testing for effect modification.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats

from .contingency import Table2x2


class StratifiedMethod(Enum):
    """Methods for stratified analysis."""
    MANTEL_HAENSZEL = "mantel_haenszel"
    DIRECT_STANDARDIZATION = "direct"
    INDIRECT_STANDARDIZATION = "indirect"


@dataclass
class StratifiedTable:
    """Container for stratified 2x2 tables."""
    tables: List[Table2x2]
    strata_names: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate that all tables have the same structure."""
        if not self.tables:
            raise ValueError("At least one table is required")
        
        if self.strata_names is None:
            self.strata_names = [f"Stratum_{i+1}" for i in range(len(self.tables))]
        elif len(self.strata_names) != len(self.tables):
            raise ValueError("Number of stratum names must match number of tables")
    
    def __len__(self) -> int:
        return len(self.tables)
    
    def __getitem__(self, idx):
        return self.tables[idx]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "n_strata": len(self.tables),
            "strata_names": self.strata_names,
            "tables": [table.to_dict() for table in self.tables]
        }


@dataclass
class MantelHaenszelResult:
    """Result object for Mantel-Haenszel analysis."""
    common_or: float
    common_rr: float
    common_rd: float
    or_ci: Tuple[float, float]
    rr_ci: Tuple[float, float]
    chi2_mh: float
    p_value: float
    cochran_q: float
    q_p_value: float
    i_squared: float
    tau_squared: float
    
    def __repr__(self) -> str:
        return f"Mantel-Haenszel OR: {self.common_or:.3f} ({self.or_ci[0]:.3f}-{self.or_ci[1]:.3f})"
    
    def summary(self) -> str:
        """Generate text summary."""
        return (f"Mantel-Haenszel Analysis:\n"
               f"  Common OR: {self.common_or:.3f} (95% CI: {self.or_ci[0]:.3f}-{self.or_ci[1]:.3f})\n"
               f"  Common RR: {self.common_rr:.3f} (95% CI: {self.rr_ci[0]:.3f}-{self.rr_ci[1]:.3f})\n"
               f"  Common RD: {self.common_rd:.3f}\n"
               f"  Test for heterogeneity: χ²={self.cochran_q:.3f}, p={self.q_p_value:.3f}\n"
               f"  I² = {self.i_squared:.1f}%, τ² = {self.tau_squared:.3f}")


@dataclass
class DirectStandardizationResult:
    """Result object for direct standardization."""
    crude_rate: float
    adjusted_rate: float
    standard_population: np.ndarray
    stratum_specific_rates: np.ndarray
    variance: float
    ci: Tuple[float, float]
    
    def __repr__(self) -> str:
        return f"Directly Adjusted Rate: {self.adjusted_rate:.3f} ({self.ci[0]:.3f}-{self.ci[1]:.3f})"


def mantel_haenszel_or(
    stratified_tables: Union[StratifiedTable, List[Table2x2]],
    confidence: float = 0.95
) -> MantelHaenszelResult:
    """
    Calculate Mantel-Haenszel pooled odds ratio.
    
    Args:
        stratified_tables: StratifiedTable or list of Table2x2 objects
        confidence: Confidence level
        
    Returns:
        MantelHaenszelResult object
        
    Example:
        >>> table1 = Table2x2(10, 20, 30, 40)
        >>> table2 = Table2x2(15, 25, 35, 45)
        >>> result = mantel_haenszel_or([table1, table2])
    """
    if isinstance(stratified_tables, list):
        stratified_tables = StratifiedTable(stratified_tables)
    
    n_strata = len(stratified_tables)
    
    # Initialize sums for MH formulas
    sum_num_or = 0.0
    sum_den_or = 0.0
    sum_num_rr = 0.0
    sum_den_rr = 0.0
    sum_rd = 0.0
    sum_var = 0.0
    
    # For heterogeneity test
    stratum_or = []
    stratum_weights = []
    
    for table in stratified_tables.tables:
        a, b, c, d = table.a, table.b, table.c, table.d
        n = table.total
        
        # MH OR numerator and denominator
        num_or = a * d / n
        den_or = b * c / n
        
        sum_num_or += num_or
        sum_den_or += den_or
        
        # MH RR
        num_rr = a * (c + d) / n
        den_rr = (a + b) * c / n
        
        sum_num_rr += num_rr
        sum_den_rr += den_rr
        
        # MH RD
        sum_rd += (a * (c + d) - c * (a + b)) / n
        
        # Variance components
        if n > 1:
            R = (a * d) / n
            S = (b * c) / n
            P = (a + d) / n
            Q = (b + c) / n
            
            sum_var += (P * R + Q * S) / 2
        
        # For heterogeneity
        if b * c > 0:
            stratum_or.append((a * d) / (b * c))
            stratum_weights.append(1 / (1/a + 1/b + 1/c + 1/d))
    
    # Calculate common measures
    common_or = sum_num_or / sum_den_or if sum_den_or > 0 else 0.0
    common_rr = sum_num_rr / sum_den_rr if sum_den_rr > 0 else 0.0
    common_rd = sum_rd / n_strata if n_strata > 0 else 0.0
    
    # Calculate CI for OR (Robins et al. method)
    if sum_var > 0:
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        log_or = np.log(common_or)
        se_log_or = np.sqrt(sum_var / (sum_num_or * sum_den_or))
        
        or_ci_lower = np.exp(log_or - z * se_log_or)
        or_ci_upper = np.exp(log_or + z * se_log_or)
    else:
        or_ci_lower, or_ci_upper = 0.0, 0.0
    
    # CI for RR
    log_rr = np.log(common_rr)
    var_log_rr = (sum_num_rr / (sum_num_rr**2) + sum_den_rr / (sum_den_rr**2))
    se_log_rr = np.sqrt(var_log_rr) if var_log_rr > 0 else 0.0
    
    rr_ci_lower = np.exp(log_rr - z * se_log_rr)
    rr_ci_upper = np.exp(log_rr + z * se_log_rr)
    
    # Test for heterogeneity (Cochran's Q)
    if len(stratum_or) > 1:
        cochran_q = _cochran_q_test(stratum_or, stratum_weights)
        df = len(stratum_or) - 1
        q_p_value = 1 - stats.chi2.cdf(cochran_q, df) if df > 0 else 1.0
        
        # I² statistic
        if cochran_q > df:
            i_squared = max(0, (cochran_q - df) / cochran_q * 100)
        else:
            i_squared = 0.0
        
        # Tau² (between-study variance)
        if cochran_q > df:
            c = sum(stratum_weights) - sum(w**2 for w in stratum_weights) / sum(stratum_weights)
            tau_squared = max(0, (cochran_q - df) / c)
        else:
            tau_squared = 0.0
    else:
        cochran_q = 0.0
        q_p_value = 1.0
        i_squared = 0.0
        tau_squared = 0.0
    
    # Mantel-Haenszel chi-square test
    chi2_mh = _mantel_haenszel_chi2(stratified_tables)
    mh_p_value = 1 - stats.chi2.cdf(chi2_mh, 1) if chi2_mh > 0 else 1.0
    
    return MantelHaenszelResult(
        common_or=common_or,
        common_rr=common_rr,
        common_rd=common_rd,
        or_ci=(or_ci_lower, or_ci_upper),
        rr_ci=(rr_ci_lower, rr_ci_upper),
        chi2_mh=chi2_mh,
        p_value=mh_p_value,
        cochran_q=cochran_q,
        q_p_value=q_p_value,
        i_squared=i_squared,
        tau_squared=tau_squared
    )


def _cochran_q_test(stratum_or: List[float], weights: List[float]) -> float:
    """Calculate Cochran's Q statistic for heterogeneity."""
    if len(stratum_or) <= 1:
        return 0.0
    
    # Inverse variance weights
    weighted_mean = sum(w * np.log(or_val) for w, or_val in zip(weights, stratum_or)) / sum(weights)
    
    Q = sum(w * (np.log(or_val) - weighted_mean)**2 for w, or_val in zip(weights, stratum_or))
    
    return Q


def _mantel_haenszel_chi2(stratified_tables: StratifiedTable) -> float:
    """Calculate Mantel-Haenszel chi-square statistic."""
    sum_num = 0.0
    sum_var = 0.0
    
    for table in stratified_tables.tables:
        a, b, c, d = table.a, table.b, table.c, table.d
        n = table.total
        
        # Expected value of a under null
        expected_a = (a + b) * (a + c) / n if n > 0 else 0
        
        sum_num += a - expected_a
        sum_var += (a + b) * (c + d) * (a + c) * (b + d) / (n**2 * (n - 1)) if n > 1 else 0
    
    if sum_var > 0:
        chi2 = sum_num**2 / sum_var
    else:
        chi2 = 0.0
    
    return chi2


def test_effect_modification(
    stratified_tables: StratifiedTable,
    method: str = "breslow_day"
) -> Dict[str, float]:
    """
    Test for effect modification (interaction) across strata.
    
    Args:
        stratified_tables: StratifiedTable object
        method: 'breslow_day' or 'woolf'
        
    Returns:
        Dictionary with test statistics
    """
    if len(stratified_tables) < 2:
        return {"statistic": 0.0, "p_value": 1.0, "df": 0}
    
    if method == "woolf":
        return _woolf_test(stratified_tables)
    else:  # breslow_day
        return _breslow_day_test(stratified_tables)


def _woolf_test(stratified_tables: StratifiedTable) -> Dict[str, float]:
    """Woolf's test for homogeneity of odds ratios."""
    stratum_or = []
    stratum_weights = []
    
    for table in stratified_tables.tables:
        if table.b * table.c > 0:
            or_val = (table.a * table.d) / (table.b * table.c)
            stratum_or.append(or_val)
            # Inverse variance weight
            weight = 1 / (1/table.a + 1/table.b + 1/table.c + 1/table.d)
            stratum_weights.append(weight)
    
    if len(stratum_or) < 2:
        return {"statistic": 0.0, "p_value": 1.0, "df": 0}
    
    # Weighted mean of log OR
    log_or = [np.log(or_val) for or_val in stratum_or]
    weighted_mean = sum(w * val for w, val in zip(stratum_weights, log_or)) / sum(stratum_weights)
    
    # Woolf's chi-square
    chi2 = sum(w * (val - weighted_mean)**2 for w, val in zip(stratum_weights, log_or))
    df = len(stratum_or) - 1
    p_value = 1 - stats.chi2.cdf(chi2, df) if df > 0 else 1.0
    
    return {
        "test": "woolf",
        "statistic": chi2,
        "p_value": p_value,
        "df": df
    }


def _breslow_day_test(stratified_tables: StratifiedTable) -> Dict[str, float]:
    """Breslow-Day test for homogeneity of odds ratios."""
    # This is a simplified implementation
    # Full BD test requires iterative fitting
    return _woolf_test(stratified_tables)  # Use Woolf as approximation


def direct_standardization(
    stratum_rates: np.ndarray,
    stratum_populations: np.ndarray,
    standard_population: np.ndarray,
    confidence: float = 0.95
) -> DirectStandardizationResult:
    """
    Perform direct standardization of rates.
    
    Args:
        stratum_rates: Rates in each stratum
        stratum_populations: Population in each stratum
        standard_population: Standard population distribution
        confidence: Confidence level
        
    Returns:
        DirectStandardizationResult object
    """
    # Validate inputs
    n_strata = len(stratum_rates)
    if len(stratum_populations) != n_strata or len(standard_population) != n_strata:
        raise ValueError("All inputs must have same length")
    
    # Crude rate
    crude_rate = np.sum(stratum_rates * stratum_populations) / np.sum(stratum_populations)
    
    # Directly adjusted rate
    adjusted_rate = np.sum(stratum_rates * standard_population) / np.sum(standard_population)
    
    # Variance of adjusted rate
    variance = np.sum((standard_population**2 * stratum_rates * (1 - stratum_rates)) / 
                     stratum_populations) / (np.sum(standard_population)**2)
    
    # Confidence interval
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    se = np.sqrt(variance)
    ci_lower = adjusted_rate - z * se
    ci_upper = adjusted_rate + z * se
    
    return DirectStandardizationResult(
        crude_rate=crude_rate,
        adjusted_rate=adjusted_rate,
        standard_population=standard_population,
        stratum_specific_rates=stratum_rates,
        variance=variance,
        ci=(ci_lower, ci_upper)
    )


def indirect_standardization(
    observed_cases: np.ndarray,
    stratum_populations: np.ndarray,
    reference_rates: np.ndarray,
    confidence: float = 0.95
) -> Dict[str, float]:
    """
    Perform indirect standardization (SMR calculation).
    
    Args:
        observed_cases: Observed cases in each stratum
        stratum_populations: Population in each stratum
        reference_rates: Reference rates in each stratum
        confidence: Confidence level
        
    Returns:
        Dictionary with SMR and other statistics
    """
    # Expected cases using reference rates
    expected_cases = np.sum(stratum_populations * reference_rates)
    total_observed = np.sum(observed_cases)
    
    # Standardized Mortality/Morbidity Ratio
    smr = total_observed / expected_cases if expected_cases > 0 else 0.0
    
    # Confidence interval for SMR (Byar's approximation)
    if total_observed >= 10:
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        ci_lower = total_observed * (1 - 1/(9*total_observed) - z/(3*np.sqrt(total_observed)))**3 / expected_cases
        ci_upper = (total_observed + 1) * (1 - 1/(9*(total_observed+1)) + z/(3*np.sqrt(total_observed+1)))**3 / expected_cases
    else:
        # Exact Poisson CI
        ci_lower = stats.chi2.ppf((1-confidence)/2, 2*total_observed) / (2*expected_cases)
        ci_upper = stats.chi2.ppf(1-(1-confidence)/2, 2*(total_observed+1)) / (2*expected_cases)
    
    return {
        "smr": smr,
        "observed_cases": float(total_observed),
        "expected_cases": float(expected_cases),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "confidence": confidence
    }


def stratified_by_variable(
    data,
    exposure_var: str,
    outcome_var: str,
    stratify_var: str
) -> StratifiedTable:
    """
    Create stratified tables from DataFrame.
    
    Args:
        data: pandas DataFrame
        exposure_var: Exposure variable name
        outcome_var: Outcome variable name
        stratify_var: Variable to stratify by
        
    Returns:
        StratifiedTable object
    """
    import pandas as pd
    
    if not hasattr(data, 'groupby'):
        raise ValueError("Data must be a pandas DataFrame or similar")
    
    tables = []
    strata_names = []
    
    for stratum, group in data.groupby(stratify_var):
        # Create 2x2 table for this stratum
        table = Table2x2(
            a=group[(group[exposure_var] == 1) & (group[outcome_var] == 1)].shape[0],
            b=group[(group[exposure_var] == 0) & (group[outcome_var] == 1)].shape[0],
            c=group[(group[exposure_var] == 1) & (group[outcome_var] == 0)].shape[0],
            d=group[(group[exposure_var] == 0) & (group[outcome_var] == 0)].shape[0]
        )
        
        tables.append(table)
        strata_names.append(str(stratum))
    
    return StratifiedTable(tables, strata_names)


#  MODULE EXPORTS 

__all__ = [
    'StratifiedMethod',
    'StratifiedTable',
    'MantelHaenszelResult',
    'DirectStandardizationResult',
    'mantel_haenszel_or',
    'test_effect_modification',
    'direct_standardization',
    'indirect_standardization',
    'stratified_by_variable'
]
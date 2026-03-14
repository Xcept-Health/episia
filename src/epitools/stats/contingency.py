"""
Contingency Core 2x2 contingency table calculations for epidemiology.

This module provides the Table2x2 class for performing epidemiological
calculations on 2x2 contingency tables, including risk ratios, odds ratios,
risk differences, and various confidence intervals.
"""

import numpy as np
from typing import Tuple, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ConfidenceMethod(Enum):
    """Methods for calculating confidence intervals."""
    
    WALD = "wald"
    DELTA = "delta"
    SCORE = "score"
    EXACT = "exact"
    
@dataclass
class RiskRatioResult:
    """Rich Reslult object for Risk Ratio calculations."""
    estimate: float
    ci_lower: float
    ci_upper: float
    methiod: str
    table: "Table2x2"
    
    def __repr__(self) -> str:
        return f"Risk Ratio: {self.estimate:.3f} ({self.ci_lower:.3f}-{self.ci_upper:.3f})"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary for easy serialization."""
        return {
            "measure": "risk_ratio",
            "estimate": self.estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "method": self.method,
            "table": self.table.to_dict()
        }
        
@dataclass
class OddsRatioResult:
    """"Rich Result object for Odds Ratio calculations."""
    estimate: float
    ci_lower: float
    ci_upper: float
    method: str
    table: "Table2x2"
  
    def __repr__(self) -> str:
        return f"Odds Ratio: {self.estimate:.3f} ({self.ci_lower:.3f}-{self.ci_upper:.3f})"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary for easy serialization."""
        return {
            "measure": "odds_ratio",
            "estimate": self.estimate,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "method": self.method,
            "table": self.table.to_dict()
        }
        

class Table2x2:
    """
    2x2 contingency table for epidemiological calculations.
    
    Represents a standard 2x2 table layout:
        +-----------+-----------+
        | Exposed   | Unexposed |
    +---+-----------+-----------+
    | Cases |     a     |     b     |
    +-------+-----------+-----------+
    | Non-cases |     c     |     d     |
    +-------+-----------+-----------+
    
    Attributes:
        a (int): Exposed cases
        b (int): Unexposed cases  
        c (int): Exposed non-cases
        d (int): Unexposed non-cases
    """
    
    __slots__ = ('a', 'b', 'c', 'd', '_cache')
    
    def __init__(self, a: int, b: int, c: int, d: int):
        """
        Initialize a 2x2 contingency table.
        
        Args:
            a: Exposed cases (cell a)
            b: Unexposed cases (cell b)
            c: Exposed non-cases (cell c)
            d: Unexposed non-cases (cell d)
            
        Raises:
            ValueError: If any cell value is negative
        """
        # Validate inputs
        if any(x < 0 for x in (a, b, c, d)):
            raise ValueError("All cell values must be non-negative")
        
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        
        # Cache for optimized repeated calculations
        self._cache: Dict[str, float] = {}    
        

    # ==================== PROPERTIES & CACHED CALCULATIONS ====================

    @property
    def total_exposed(self) -> int:
        """Total number of exposed individuals (a + c)."""
        return self.a + self.c
    
    @property
    def total_unexposed(self) -> int:
        """Total number of unexposed individuals (b + d)."""
        return self.b + self.d
    
    @property
    def total_cases(self) -> int:
        """Total number of cases (a + b)."""
        return self.a + self.b
    
    @property
    def total_non_cases(self) -> int:
        """Total number of non-cases (c + d)."""
        return self.c + self.d
    
    @property
    def total(self) -> int:
        """Total number of individuals (a + b + c + d)."""
        return self.a + self.b + self.c + self.d
    
    @property
    def risk_exposed(self) -> float:
        """Risk (incidence proportion) in exposed group: a / (a + c)."""
        key = "risk_exposed"
        if key not in self._cache:
            if self.total_exposed == 0:
                self._cache[key] = 0.0
            else:
                self._cache[key] = self.a / self.total_exposed
        return self._cache[key]
    
    @property
    def risk_unexposed(self) -> float:
        """Risk (incidence proportion) in unexposed group: b / (b + d)."""
        key = "risk_unexposed"
        if key not in self._cache:
            if self.total_unexposed == 0:
                self._cache[key] = 0.0
            else:
                self._cache[key] = self.b / self.total_unexposed
        return self._cache[key]
    
    @property
    def odds_exposed(self) -> float:
        """Odds in exposed group: a / c."""
        key = "odds_exposed"
        if key not in self._cache:
            if self.c == 0:
                # Handle division by zero
                self._cache[key] = float('inf') if self.a > 0 else 0.0
            else:
                self._cache[key] = self.a / self.c
        return self._cache[key]
    
    @property
    def odds_unexposed(self) -> float:
        """Odds in unexposed group: b / d."""
        key = "odds_unexposed"
        if key not in self._cache:
            if self.d == 0:
                # Handle division by zero
                self._cache[key] = float('inf') if self.b > 0 else 0.0
            else:
                self._cache[key] = self.b / self.d
        return self._cache[key]
    
    # ==================== CORE EPIDEMIOLOGICAL MEASURES ====================
    
    def risk_ratio(self, 
                   method: ConfidenceMethod = ConfidenceMethod.WALD,
                   confidence: float = 0.95) -> RiskRatioResult:
        """
        Calculate risk ratio (relative risk) with confidence interval.
        
        Risk Ratio = (a/(a+c)) / (b/(b+d))
        
        Args:
            method: Method for confidence interval calculation
            confidence: Confidence level (default: 0.95 for 95% CI)
            
        Returns:
            RiskRatioResult object containing estimate and confidence interval
            
        Example:
            >>> table = Table2x2(10, 20, 30, 40)
            >>> result = table.risk_ratio()
            >>> print(result.estimate)
            0.6667
        """
        
        # Calculate point estimate
        if self.risk_unexposed == 0:
            rr = float('inf') if self.risk_exposed > 0 else 0.0
        else:
            rr = self.risk_exposed / self.risk_unexposed
        
        # Calculate confidence interval based on method
        if method == ConfidenceMethod.WALD:
            ci_lower, ci_upper = self._wald_ci_rr(rr, confidence)
        elif method == ConfidenceMethod.SCORE:
            ci_lower, ci_upper = self._score_ci_rr(confidence)
        else:
            # Default to delta method
            ci_lower, ci_upper = self._delta_ci_rr(rr, confidence)
        
        return RiskRatioResult(
            estimate=rr,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            method=method.value,
            table=self
        )
        
    def odds_ratio(self,
                   method: ConfidenceMethod = ConfidenceMethod.WALD,
                   confidence: float = 0.95) -> OddsRatioResult:
        """
        Calculate odds ratio with confidence interval.
        
        Odds Ratio = (a/c) / (b/d) = (a*d) / (b*c)
        
        Args:
            method: Method for confidence interval calculation
            confidence: Confidence level (default: 0.95 for 95% CI)
            
        Returns:
            OddsRatioResult object containing estimate and confidence interval
            
        Example:
            >>> table = Table2x2(10, 20, 30, 40)
            >>> result = table.odds_ratio()
            >>> print(result.estimate)
            0.6667
        """
        
        # Calculate point estimate
        if self.b * self.c == 0:
            # Handle cases with zero cells
            if self.a * self.d > 0:
                or_est = float('inf')
            else:
                or_est = 0.0
        else:
            or_est = (self.a * self.d) / (self.b * self.c)
        
        # Calculate confidence interval
        if method == ConfidenceMethod.EXACT:
            ci_lower, ci_upper = self._exact_ci_or(confidence)
        else:
            ci_lower, ci_upper = self._wald_ci_or(or_est, confidence)
        
        return OddsRatioResult(
            estimate=or_est,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            method=method.value,
            table=self
        )
        
    def risk_difference(self, confidence: float = 0.95) -> Dict[str, float]:
        """
        Calculate risk difference (attributable risk) with confidence interval.
        
        Risk Difference = Risk_exposed - Risk_unexposed
        
        Args:
            confidence: Confidence level (default: 0.95)
            
        Returns:
            Dictionary with 'estimate', 'ci_lower', and 'ci_upper'
        """
        
        rd = self.risk_exposed - self.risk_unexposed
        
        # Wald-type CI for risk difference
        se = np.sqrt(
            (self.risk_exposed * (1 - self.risk_exposed) / self.total_exposed) +
            (self.risk_unexposed * (1 - self.risk_unexposed) / self.total_unexposed)
        )
        
        z = self._z_score(confidence)
        ci_lower = rd - z * se
        ci_upper = rd + z * se
        
        return {
            "measure": "risk_difference",
            "estimate": rd,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "confidence": confidence
        }
        
    # ==================== ATTRIBUTABLE FRACTION MEASURES ====================
    
    def attributable_fraction_exposed(self) -> float:
        """
        Calculate attributable fraction among the exposed.
        
        AF_exposed = (RR - 1) / RR
        Represents proportion of cases among exposed attributable to exposure.
        
        Returns:
            Attributable fraction (range: -∞ to 1)
        """
        rr = self.risk_ratio().estimate
        if rr <= 0:
            return 0.0
        return (rr - 1) / rr  

    # ==================== STATISTICAL TESTS ====================
    
    def chi_square(self, correction: bool = True) -> Dict[str, float]:
        """
        Calculate chi-square test for association.
        
        Args:
            correction: Apply Yates' continuity correction if True
            
        Returns:
            Dictionary with 'chi2', 'p_value', and 'df' (degrees of freedom)
        """
        # Expected frequencies
        total = self.total
        e_a = (self.total_cases * self.total_exposed) / total
        e_b = (self.total_cases * self.total_unexposed) / total
        e_c = (self.total_non_cases * self.total_exposed) / total
        e_d = (self.total_non_cases * self.total_unexposed) / total
        
        if correction:
            # Yates' corrected chi-square
            chi2 = (
                (abs(self.a - e_a) - 0.5)**2 / e_a +
                (abs(self.b - e_b) - 0.5)**2 / e_b +
                (abs(self.c - e_c) - 0.5)**2 / e_c +
                (abs(self.d - e_d) - 0.5)**2 / e_d
            )
        else:
            # Pearson chi-square
            chi2 = (
                (self.a - e_a)**2 / e_a +
                (self.b - e_b)**2 / e_b +
                (self.c - e_c)**2 / e_c +
                (self.d - e_d)**2 / e_d
            )
        
        # p-value from chi-square distribution with 1 degree of freedom
        from scipy import stats
        p_value = 1 - stats.chi2.cdf(chi2, df=1)
        
        return {
            "chi2": chi2,
            "p_value": p_value,
            "df": 1,
            "correction": "yates" if correction else "pearson"
        }
        
    def fisher_exact(self) -> Dict[str, float]:
        """
        Perform Fisher's exact test (especially for small samples).
        
        Returns:
            Dictionary with 'odds_ratio', 'p_value' (two-sided)
        """
        from scipy import stats
        
        oddsratio, p_value = stats.fisher_exact([
            [self.a, self.b],
            [self.c, self.d]
        ])
        
        return {
            "odds_ratio": oddsratio,
            "p_value": p_value,
            "test": "fisher_exact"
        }
        
        # ==================== CONFIDENCE INTERVAL METHODS ====================
        
    def _wald_ci_rr(self, rr: float, confidence: float) -> Tuple[float, float]:
        """Wald confidence interval for risk ratio."""
        if rr <= 0:
            return 0.0, 0.0
        
        # Standard error on log scale
        var_log_rr = (
            (1/self.a - 1/self.total_exposed) +
            (1/self.b - 1/self.total_unexposed)
        )
        
        se_log_rr = np.sqrt(max(var_log_rr, 0))
        z = self._z_score(confidence)
        
        log_ci_lower = np.log(rr) - z * se_log_rr
        log_ci_upper = np.log(rr) + z * se_log_rr
        
        return np.exp(log_ci_lower), np.exp(log_ci_upper)
    
    def _score_ci_rr(self, confidence: float) -> Tuple[float, float]:
        """Score confidence interval for risk ratio."""
        # This is a simplified version - full implementation would be more complex
        rr_result = self.risk_ratio()
        return rr_result.ci_lower, rr_result.ci_upper
    
    def _delta_ci_rr(self, rr: float, confidence: float) -> Tuple[float, float]:
        """Delta method confidence interval for risk ratio."""
        # Similar to Wald but with different variance estimator
        return self._wald_ci_rr(rr, confidence)
    
    def _wald_ci_or(self, or_est: float, confidence: float) -> Tuple[float, float]:
        """Wald confidence interval for odds ratio."""
        if or_est <= 0:
            return 0.0, 0.0
        
        # Standard error on log scale (Woolf's method)
        if 0 in (self.a, self.b, self.c, self.d):
            # Add 0.5 to all cells for zero-cell correction (Haldane-Anscombe)
            a = self.a + 0.5
            b = self.b + 0.5
            c = self.c + 0.5
            d = self.d + 0.5
            or_est = (a * d) / (b * c)
        else:
            a, b, c, d = self.a, self.b, self.c, self.d
        
        var_log_or = 1/a + 1/b + 1/c + 1/d
        se_log_or = np.sqrt(var_log_or)
        z = self._z_score(confidence)
        
        log_ci_lower = np.log(or_est) - z * se_log_or
        log_ci_upper = np.log(or_est) + z * se_log_or
        
        return np.exp(log_ci_lower), np.exp(log_ci_upper)
    
    def _exact_ci_or(self, confidence: float) -> Tuple[float, float]:
        """Exact (conditional maximum likelihood) CI for odds ratio."""
        # For now, fall back to Woolf's method with correction
        # Full exact implementation would require more complex computation
        return self._wald_ci_or(self.odds_ratio().estimate, confidence)
    
    def _z_score(self, confidence: float) -> float:
        """Get z-score for given confidence level."""
        from scipy import stats
        alpha = 1 - confidence
        return stats.norm.ppf(1 - alpha/2)
    
    # ==================== UTILITY METHODS ====================

    def to_dict(self) -> Dict[str, int]:
        """Convert table to dictionary representation."""
        return {
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
            "total": self.total
        }
    
    def __repr__(self) -> str:
        return (f"Table2x2(a={self.a}, b={self.b}, c={self.c}, d={self.d})")
    
    def summary(self) -> Dict[str, Union[float, int, Dict]]:
        """
        Generate comprehensive summary of all calculations.
        
        Returns:
            Dictionary with all epidemiological measures
        """
        rr_result = self.risk_ratio()
        or_result = self.odds_ratio()
        rd_result = self.risk_difference()
        chi2_result = self.chi_square()
        
        return {
            "table": self.to_dict(),
            "risks": {
                "exposed": self.risk_exposed,
                "unexposed": self.risk_unexposed
            },
            "odds": {
                "exposed": self.odds_exposed,
                "unexposed": self.odds_unexposed
            },
            "risk_ratio": rr_result.to_dict(),
            "odds_ratio": or_result.to_dict(),
            "risk_difference": rd_result,
            "attributable_fractions": {
                "exposed": self.attributable_fraction_exposed(),
                "population": self.attributable_fraction_population()
            },
            "chi_square": chi2_result,
            "fisher_exact": self.fisher_exact()
        }

# ==================== CONVENIENCE FUNCTIONS ====================

def risk_ratio(a: int, b: int, c: int, d: int, **kwargs) -> RiskRatioResult:
    """
    Convenience function to calculate risk ratio from raw counts.
    
    Args:
        a, b, c, d: 2x2 table cell counts
        **kwargs: Passed to Table2x2.risk_ratio()
        
    Returns:
        RiskRatioResult object
        
    Example:
        >>> result = risk_ratio(10, 20, 30, 40)
        >>> print(result.estimate)
    """
    table = Table2x2(a, b, c, d)
    return table.risk_ratio(**kwargs)

def odds_ratio(a: int, b: int, c: int, d: int, **kwargs) -> OddsRatioResult:
    """
    Convenience function to calculate odds ratio from raw counts.
    
    Args:
        a, b, c, d: 2x2 table cell counts
        **kwargs: Passed to Table2x2.odds_ratio()
        
    Returns:
        OddsRatioResult object
    """
    table = Table2x2(a, b, c, d)
    return table.odds_ratio(**kwargs)


def from_dataframe(df, exposed_col: str, outcome_col: str) -> Table2x2:
    """
    Create Table2x2 from pandas DataFrame.
    
    Args:
        df: pandas DataFrame
        exposed_col: Column name for exposure status (True/False or 1/0)
        outcome_col: Column name for outcome status (True/False or 1/0)
        
    Returns:
        Table2x2 object
    """
    # Ensure boolean-like columns
    df = df.copy()
    for col in [exposed_col, outcome_col]:
        if df[col].dtype != bool:
            df[col] = df[col].astype(bool)
    
    # Calculate 2x2 counts
    a = df[df[exposed_col] & df[outcome_col]].shape[0]  # Exposed cases
    b = df[~df[exposed_col] & df[outcome_col]].shape[0]  # Unexposed cases
    c = df[df[exposed_col] & ~df[outcome_col]].shape[0]  # Exposed non-cases
    d = df[~df[exposed_col] & ~df[outcome_col]].shape[0] # Unexposed non-cases
    
    return Table2x2(a, b, c, d)


# ==================== MODULE EXPORTS ====================

__all__ = [
    'Table2x2',
    'RiskRatioResult',
    'OddsRatioResult',
    'ConfidenceMethod',
    'risk_ratio',
    'odds_ratio',
    'from_dataframe'
]
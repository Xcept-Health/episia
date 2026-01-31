# epitools/stats/__init__.py
"""
Statistics module for epidemiological calculations.
"""

# Import from contingency
from .contingency import (
    Table2x2,
    RiskRatioResult,
    OddsRatioResult,
    ConfidenceMethod,
    risk_ratio,
    odds_ratio,
    from_dataframe
)

# Import from descriptive
from .descriptive import (
    CI_Method,
    ProportionResult,
    MeanResult,
    proportion_ci,
    mean_ci,
    incidence_rate,
    attack_rate,
    prevalence,
    median_ci,
    interquartile_range
)

# Import from samplesize
from .samplesize import (
    StudyDesign,
    TestType,
    SampleSizeResult,
    sample_size_risk_ratio,
    sample_size_risk_difference,
    sample_size_odds_ratio,
    sample_size_sensitivity_specificity,
    sample_size_single_proportion,
    power_calculation,
    fleiss_correction,
    design_effect_deff,
    calculate_sample_size
)

__all__ = [
    # From contingency
    'Table2x2',
    'RiskRatioResult',
    'OddsRatioResult',
    'ConfidenceMethod',
    'risk_ratio',
    'odds_ratio',
    'from_dataframe',
    
    # From descriptive
    'CI_Method',
    'ProportionResult',
    'MeanResult',
    'proportion_ci',
    'mean_ci',
    'incidence_rate',
    'attack_rate',
    'prevalence',
    'median_ci',
    'interquartile_range',
    
    # From samplesize
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
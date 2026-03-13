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

# Import from diagnostic
from .diagnostic import (
    DiagnosticMeasure,
    DiagnosticResult,
    ROCResult,
    diagnostic_test_2x2,
    diagnostic_from_data,
    roc_analysis,
    likelihood_ratio_ci,
    predictive_values_from_sens_spec,
    fagan_nomogram,
    diagnostic_accuracy_ci,
    compare_diagnostic_tests,
    optimal_threshold_grid_search
)

# Import from stratified
from .stratified import (
    StratifiedMethod,
    StratifiedTable,
    MantelHaenszelResult,
    DirectStandardizationResult,
    mantel_haenszel_or,
    test_effect_modification,
    direct_standardization,
    indirect_standardization,
    stratified_by_variable
)

# Import from time_series
from .time_series import (
    TimeAggregation,
    TrendMethod,
    EpidemicCurve,
    TimeSeriesResult,
    calculate_incidence,
    calculate_attack_rate,
    epidemic_curve,
    moving_average,
    loess_smoothing,
    detect_epidemic_threshold,
    reproductive_number,
    seasonality_decomposition,
    exponential_growth_rate,
    nowcasting,
    cumulative_curve,
    detect_peaks
)

# Import from regression
from .regression import (
    RegressionType,
    ModelSelection,
    RegressionResult,
    logistic_regression,
    poisson_regression,
    likelihood_ratio_test,
    hosmer_lemeshow_test,
    calculate_vif,
    stepwise_selection,
    roc_auc_from_logistic,
    interaction_term
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
    'calculate_sample_size',
    
    # From diagnostic
    'DiagnosticMeasure',
    'DiagnosticResult',
    'ROCResult',
    'diagnostic_test_2x2',
    'diagnostic_from_data',
    'roc_analysis',
    'likelihood_ratio_ci',
    'predictive_values_from_sens_spec',
    'fagan_nomogram',
    'diagnostic_accuracy_ci',
    'compare_diagnostic_tests',
    'optimal_threshold_grid_search',
    
    # From stratified
    'StratifiedMethod',
    'StratifiedTable',
    'MantelHaenszelResult',
    'DirectStandardizationResult',
    'mantel_haenszel_or',
    'test_effect_modification',
    'direct_standardization',
    'indirect_standardization',
    'stratified_by_variable',
    
    # From time_series
    'TimeAggregation',
    'TrendMethod',
    'EpidemicCurve',
    'TimeSeriesResult',
    'calculate_incidence',
    'calculate_attack_rate',
    'epidemic_curve',
    'moving_average',
    'loess_smoothing',
    'detect_epidemic_threshold',
    'reproductive_number',
    'seasonality_decomposition',
    'exponential_growth_rate',
    'nowcasting',
    'cumulative_curve',
    'detect_peaks',
    
    # From regression
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
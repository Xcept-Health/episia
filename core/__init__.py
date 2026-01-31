"""
Core module for EpiTools - Foundation utilities and technical infrastructure.

This module provides the technical foundation for EpiTools, including:
- Optimized calculators with caching
- Data validation functions
- Custom exceptions
- Configuration constants
- Utility functions and decorators
"""

from .calculator import (
    CacheStrategy,
    CalculationStats,
    BaseCalculator,
    EpidemiologicalCalculator,
    MatrixCalculator,
    epi_calculator,
    matrix_calculator,
    cached_function
)

from .validator import (
    ValidationError,
    validate_2x2_table,
    validate_proportion,
    validate_confidence_level,
    validate_sample_size,
    validate_dataframe,
    validate_binary_variable,
    validate_date_series,
    validate_numeric_array,
    validate_model_parameters,
    check_convergence,
    validate_positive
)

from .exceptions import (
    EpiToolsError,
    ValidationError,
    ConvergenceError,
    ConfigurationError,
    DataError,
    ModelError,
    StatisticalError,
    DimensionError,
    ParameterError,
    ComputationError,
    FileError,
    PlotError,
    WarningManager
)

from .constants import (
    ConfidenceLevel,
    AlphaLevel,
    PowerLevel,
    DEFAULT_CONFIDENCE,
    DEFAULT_ALPHA,
    DEFAULT_POWER,
    EPSILON,
    MAX_ITERATIONS,
    CONVERGENCE_TOL,
    CHI_SQUARE_SMALL_SAMPLE,
    FISHER_EXACT_THRESHOLD,
    NORMAL_APPROXIMATION_N,
    MEAN_INCUBATION_COVID,
    MEAN_INFECTIOUS_PERIOD_COVID,
    BASIC_REPRODUCTION_COVID,
    WHO_STANDARD_POPULATION,
    EUROPEAN_STANDARD_POPULATION,
    COVID19_PARAMS,
    INFLUENZA_PARAMS,
    EBOLA_PARAMS,
    ConfidenceIntervalMethod,
    RiskRatioMethod,
    OddsRatioMethod,
    PlotStyle,
    ColorPalette,
    DEFAULT_FIGSIZE,
    DEFAULT_DPI,
    DEFAULT_FONTSIZE,
    DEFAULT_COLOR_PALETTE,
    DEFAULT_PLOT_STYLE,
    EPITOOLS_CONFIG,
    get_config,
    set_config
)

from .utilities import (
    timer,
    validate_input,
    deprecated,
    memoize,
    safe_divide,
    clip_values,
    format_number,
    format_pvalue,
    create_bins,
    logit,
    expit,
    standardize,
    winsorize,
    numpy_errstate,
    pandas_display_options,
    is_numeric,
    is_integer_array,
    is_binary_array,
    sanitize_filename,
    set_random_seed,
    generate_random_id
)

__all__ = [
    # From calculator
    'CacheStrategy',
    'CalculationStats',
    'BaseCalculator',
    'EpidemiologicalCalculator',
    'MatrixCalculator',
    'epi_calculator',
    'matrix_calculator',
    'cached_function',
    
    # From validator
    'ValidationError',
    'validate_2x2_table',
    'validate_proportion',
    'validate_confidence_level',
    'validate_sample_size',
    'validate_dataframe',
    'validate_binary_variable',
    'validate_date_series',
    'validate_numeric_array',
    'validate_model_parameters',
    'check_convergence',
    'validate_positive',
    
    # From exceptions
    'EpiToolsError',
    'ValidationError',
    'ConvergenceError',
    'ConfigurationError',
    'DataError',
    'ModelError',
    'StatisticalError',
    'DimensionError',
    'ParameterError',
    'ComputationError',
    'FileError',
    'PlotError',
    'WarningManager',
    
    # From constants
    'ConfidenceLevel',
    'AlphaLevel',
    'PowerLevel',
    'DEFAULT_CONFIDENCE',
    'DEFAULT_ALPHA',
    'DEFAULT_POWER',
    'EPSILON',
    'MAX_ITERATIONS',
    'CONVERGENCE_TOL',
    'CHI_SQUARE_SMALL_SAMPLE',
    'FISHER_EXACT_THRESHOLD',
    'NORMAL_APPROXIMATION_N',
    'MEAN_INCUBATION_COVID',
    'MEAN_INFECTIOUS_PERIOD_COVID',
    'BASIC_REPRODUCTION_COVID',
    'WHO_STANDARD_POPULATION',
    'EUROPEAN_STANDARD_POPULATION',
    'COVID19_PARAMS',
    'INFLUENZA_PARAMS',
    'EBOLA_PARAMS',
    'ConfidenceIntervalMethod',
    'RiskRatioMethod',
    'OddsRatioMethod',
    'PlotStyle',
    'ColorPalette',
    'DEFAULT_FIGSIZE',
    'DEFAULT_DPI',
    'DEFAULT_FONTSIZE',
    'DEFAULT_COLOR_PALETTE',
    'DEFAULT_PLOT_STYLE',
    'EPITOOLS_CONFIG',
    'get_config',
    'set_config',
    
    # From utilities
    'timer',
    'validate_input',
    'deprecated',
    'memoize',
    'safe_divide',
    'clip_values',
    'format_number',
    'format_pvalue',
    'create_bins',
    'logit',
    'expit',
    'standardize',
    'winsorize',
    'numpy_errstate',
    'pandas_display_options',
    'is_numeric',
    'is_integer_array',
    'is_binary_array',
    'sanitize_filename',
    'set_random_seed',
    'generate_random_id'
]
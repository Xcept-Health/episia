"""
This module defines constants used throughout Episia, including
statistical thresholds, default parameters, and configuration options.
"""

from enum import Enum
from typing import Dict, Any
import numpy as np


# STATISTICAL CONSTANTS 

class ConfidenceLevel(float, Enum):
    """Common confidence levels."""
    P90 = 0.90
    P95 = 0.95
    P99 = 0.99
    P999 = 0.999


class AlphaLevel(float, Enum):
    """Common alpha levels for significance testing."""
    ALPHA_010 = 0.10
    ALPHA_005 = 0.05
    ALPHA_001 = 0.01
    ALPHA_0001 = 0.001


class PowerLevel(float, Enum):
    """Common statistical power levels."""
    POWER_080 = 0.80
    POWER_085 = 0.85
    POWER_090 = 0.90
    POWER_095 = 0.95


# Default values
DEFAULT_CONFIDENCE = ConfidenceLevel.P95
DEFAULT_ALPHA = AlphaLevel.ALPHA_005
DEFAULT_POWER = PowerLevel.POWER_080

# Numerical tolerance
EPSILON = 1e-10
MAX_ITERATIONS = 1000
CONVERGENCE_TOL = 1e-6

# Statistical thresholds
CHI_SQUARE_SMALL_SAMPLE = 5  # Expected cell count for chi-square
FISHER_EXACT_THRESHOLD = 20  # Sample size threshold for Fisher's exact
NORMAL_APPROXIMATION_N = 30  # Sample size for normal approximation

# Epidemiological constants
MEAN_INCUBATION_COVID = 5.2  # days
MEAN_INFECTIOUS_PERIOD_COVID = 7.0  # days
BASIC_REPRODUCTION_COVID = 2.5  # R0 for COVID-19

# Standard populations for age standardization
# WHO World Standard Population 2000-2025
WHO_STANDARD_POPULATION = np.array([
    1000, 900, 900, 900, 900,  # 0-4, 5-9, 10-14, 15-19, 20-24
    800, 800, 700, 600, 500,   # 25-29, 30-34, 35-39, 40-44, 45-49
    400, 400, 300, 200, 100,   # 50-54, 55-59, 60-64, 65-69, 70-74
    50, 30, 20, 10, 5          # 75-79, 80-84, 85-89, 90-94, 95+
])

# European Standard Population 2013
EUROPEAN_STANDARD_POPULATION = np.array([
    1000, 900, 900, 900, 800,  # 0-4, 5-9, 10-14, 15-19, 20-24
    800, 800, 700, 700, 700,   # 25-29, 30-34, 35-39, 40-44, 45-49
    700, 700, 600, 500, 400,   # 50-54, 55-59, 60-64, 65-69, 70-74
    300, 200, 100, 50, 20      # 75-79, 80-84, 85-89, 90-94, 95+
])


# DISEASE-SPECIFIC CONSTANTS 

COVID19_PARAMS = {
    "incubation_period": {
        "mean": 5.2,
        "std": 3.5,
        "distribution": "lognormal"
    },
    "infectious_period": {
        "mean": 7.0,
        "std": 3.0,
        "distribution": "gamma"
    },
    "basic_reproduction": {
        "mean": 2.5,
        "range": (1.5, 3.5)
    },
    "case_fatality_rate": {
        "global": 0.02,
        "by_age": {
            "0-9": 0.001,
            "10-19": 0.001,
            "20-29": 0.002,
            "30-39": 0.004,
            "40-49": 0.010,
            "50-59": 0.035,
            "60-69": 0.095,
            "70-79": 0.180,
            "80+": 0.300
        }
    }
}

INFLUENZA_PARAMS = {
    "incubation_period": {
        "mean": 1.4,
        "std": 0.8,
        "distribution": "gamma"
    },
    "infectious_period": {
        "mean": 3.0,
        "std": 1.0,
        "distribution": "gamma"
    },
    "basic_reproduction": {
        "mean": 1.3,
        "range": (1.1, 1.5)
    }
}

EBOLA_PARAMS = {
    "incubation_period": {
        "mean": 9.0,
        "std": 5.0,
        "distribution": "lognormal"
    },
    "infectious_period": {
        "mean": 10.0,
        "std": 4.0,
        "distribution": "gamma"
    },
    "basic_reproduction": {
        "mean": 1.8,
        "range": (1.5, 2.2)
    },
    "case_fatality_rate": 0.50
}


# CALCULATION METHODS 

class ConfidenceIntervalMethod(str, Enum):
    """Methods for confidence interval calculation."""
    WALD = "wald"
    WILSON = "wilson"
    AGRESTI_COULL = "agresti_coull"
    JEFFREYS = "jeffreys"
    CLOPPER_PEARSON = "clopper_pearson"
    DELTA = "delta"
    BOOTSTRAP = "bootstrap"


class RiskRatioMethod(str, Enum):
    """Methods for risk ratio calculation."""
    WALD = "wald"
    DELTA = "delta"
    SCORE = "score"
    BOOTSTRAP = "bootstrap"


class OddsRatioMethod(str, Enum):
    """Methods for odds ratio calculation."""
    WALD = "wald"
    CORNELL = "cornell"
    FLEISS = "fleiss"
    GART = "gart"
    EXACT = "exact"


# VISUALIZATION CONSTANTS 

class PlotStyle(str, Enum):
    """Plot style presets."""
    SCIENTIFIC = "scientific"
    MINIMAL = "minimal"
    DARK = "dark"
    COLORBLIND = "colorblind"
    PRESENTATION = "presentation"


class ColorPalette(str, Enum):
    """Color palette options."""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    CIVIDIS = "cividis"
    TAB10 = "tab10"
    SET2 = "set2"
    DARK2 = "dark2"


# Default plotting parameters
DEFAULT_FIGSIZE = (10, 6)
DEFAULT_DPI = 100
DEFAULT_FONTSIZE = 12
DEFAULT_COLOR_PALETTE = ColorPalette.VIRIDIS
DEFAULT_PLOT_STYLE = PlotStyle.SCIENTIFIC


# CONFIGURATION DICTIONARY 

EPISIA_CONFIG: Dict[str, Any] = {
    # Statistical defaults
    "statistics": {
        "confidence_level": DEFAULT_CONFIDENCE,
        "alpha_level": DEFAULT_ALPHA,
        "power_level": DEFAULT_POWER,
        "convergence_tol": CONVERGENCE_TOL,
        "max_iterations": MAX_ITERATIONS
    },
    
    # Visualization defaults
    "visualization": {
        "figure_size": DEFAULT_FIGSIZE,
        "dpi": DEFAULT_DPI,
        "font_size": DEFAULT_FONTSIZE,
        "color_palette": DEFAULT_COLOR_PALETTE,
        "plot_style": DEFAULT_PLOT_STYLE
    },
    
    # Computational defaults
    "computation": {
        "use_cache": True,
        "cache_size": 1000,
        "parallel_processing": False,
        "n_jobs": 1
    },
    
    # Output defaults
    "output": {
        "decimal_places": 3,
        "pvalue_format": "auto",  # 'auto', 'scientific', 'decimal'
        "show_confidence_intervals": True,
        "include_sample_sizes": True
    }
}


def get_config(key: str = None) -> Any:
    """
    Get configuration value(s).
    
    Args:
        key: Configuration key (e.g., 'statistics.confidence_level')
        
    Returns:
        Configuration value or dictionary
    """
    if key is None:
        return EPISIA_CONFIG.copy()
    
    # Handle nested keys
    keys = key.split('.')
    value = EPISIA_CONFIG
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise KeyError(f"Configuration key not found: {key}")
    
    return value


def set_config(key: str, value: Any) -> None:
    """
    Set configuration value.
    
    Args:
        key: Configuration key (e.g., 'statistics.confidence_level')
        value: New value
    """
    keys = key.split('.')
    config = EPISIA_CONFIG
    
    # Navigate to nested dictionary
    for k in keys[:-1]:
        if k not in config:
            config[k] = {}
        config = config[k]
    
    # Set value
    config[keys[-1]] = value
"""
This module provides functions for analyzing temporal patterns in
epidemiological data, including epidemic curves, incidence rates,
and temporal trend analysis.
"""

import numpy as np
from typing import Union, Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import warnings
from scipy import stats, signal
import pandas as pd


class TimeAggregation(Enum):
    """Time aggregation methods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class TrendMethod(Enum):
    """Methods for trend analysis."""
    LINEAR = "linear"
    LOESS = "loess"
    SPLINE = "spline"
    MOVING_AVERAGE = "moving_average"


@dataclass
class EpidemicCurve:
    """Container for epidemic curve data."""
    dates: np.ndarray
    counts: np.ndarray
    aggregated: bool
    aggregation: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def __post_init__(self):
        """Validate data."""
        if len(self.dates) != len(self.counts):
            raise ValueError("Dates and counts must have same length")
        
        if self.metadata is None:
            self.metadata = {}
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame({
            'date': self.dates,
            'count': self.counts
        })
    
    def summary(self) -> Dict:
        """Calculate summary statistics."""
        return {
            "total_cases": int(np.sum(self.counts)),
            "mean_daily": float(np.mean(self.counts)),
            "max_daily": int(np.max(self.counts)),
            "peak_date": self.dates[np.argmax(self.counts)],
            "duration_days": len(self.counts),
            "start_date": self.dates[0],
            "end_date": self.dates[-1]
        }


@dataclass
class TimeSeriesResult:
    """Result object for time series analysis."""
    dates: np.ndarray
    observed: np.ndarray
    predicted: Optional[np.ndarray] = None
    residuals: Optional[np.ndarray] = None
    trend: Optional[np.ndarray] = None
    seasonality: Optional[np.ndarray] = None
    method: Optional[str] = None
    metrics: Optional[Dict] = None
    
    def __repr__(self) -> str:
        if self.metrics:
            return f"TimeSeries (R²={self.metrics.get('r_squared', 0):.3f})"
        return "TimeSeriesResult"
    
    def plot_data(self) -> Dict:
        """Prepare data for plotting."""
        data = {
            "dates": self.dates,
            "observed": self.observed,
            "trend": self.trend
        }
        
        if self.predicted is not None:
            data["predicted"] = self.predicted
        
        return data


def calculate_incidence(
    cases: np.ndarray,
    population: Union[float, np.ndarray],
    time_period: float = 1.0
) -> np.ndarray:
    """
    Calculate incidence rates.
    
    Args:
        cases: Number of cases
        population: Population at risk (scalar or array)
        time_period: Time period for rate (default: 1 unit)
        
    Returns:
        Incidence rates per time period
        
    Example:
        >>> calculate_incidence([10, 20, 30], 1000)
        array([0.01, 0.02, 0.03])  # per time unit
    """
    cases = np.asarray(cases, dtype=float)
    population = np.asarray(population, dtype=float)
    
    if np.any(population <= 0):
        raise ValueError("Population must be positive")
    
    incidence = cases / population * time_period
    
    return incidence


def calculate_attack_rate(
    cases: np.ndarray,
    population: Union[float, np.ndarray]
) -> np.ndarray:
    """
    Calculate attack rates (cumulative incidence).
    
    Args:
        cases: Cumulative cases over time
        population: Population at risk
        
    Returns:
        Attack rates (proportion)
    """
    cases = np.asarray(cases, dtype=float)
    population = np.asarray(population, dtype=float)
    
    if np.any(population <= 0):
        raise ValueError("Population must be positive")
    
    attack_rate = cases / population
    
    # Ensure values are between 0 and 1
    attack_rate = np.clip(attack_rate, 0, 1)
    
    return attack_rate


def epidemic_curve(
    dates: np.ndarray,
    counts: np.ndarray,
    aggregation: TimeAggregation = TimeAggregation.DAILY,
    fill_missing: bool = True
) -> EpidemicCurve:
    """
    Create epidemic curve from date-case data.
    
    Args:
        dates: Array of dates
        counts: Array of case counts
        aggregation: Time aggregation level
        fill_missing: Fill missing dates with zeros
        
    Returns:
        EpidemicCurve object
    """
    # Convert to pandas Series for easy manipulation
    if not isinstance(dates, pd.DatetimeIndex):
        dates = pd.to_datetime(dates)
    
    series = pd.Series(counts, index=dates)
    
    # Resample based on aggregation
    if aggregation == TimeAggregation.WEEKLY:
        resampled = series.resample('W').sum()
        agg_label = "weekly"
    elif aggregation == TimeAggregation.MONTHLY:
        resampled = series.resample('M').sum()
        agg_label = "monthly"
    elif aggregation == TimeAggregation.YEARLY:
        resampled = series.resample('Y').sum()
        agg_label = "yearly"
    else:  # DAILY
        if fill_missing:
            # Create complete date range
            full_range = pd.date_range(start=series.index.min(), 
                                      end=series.index.max(), 
                                      freq='D')
            resampled = series.reindex(full_range, fill_value=0)
        else:
            resampled = series
        agg_label = "daily"
    
    return EpidemicCurve(
        dates=resampled.index.values,
        counts=resampled.values,
        aggregated=aggregation != TimeAggregation.DAILY,
        aggregation=agg_label
    )


def moving_average(
    data: np.ndarray,
    window: int = 7,
    center: bool = True
) -> np.ndarray:
    """
    Calculate moving average for smoothing time series.
    
    Args:
        data: Time series data
        window: Window size for moving average
        center: Whether to center the window
        
    Returns:
        Smoothed time series
    """
    if window <= 0:
        raise ValueError("Window must be positive")
    
    if window > len(data):
        window = len(data)
        warnings.warn(f"Window reduced to data length: {window}")
    
    # Use pandas for robust handling
    series = pd.Series(data)
    smoothed = series.rolling(window=window, center=center, min_periods=1).mean()
    
    return smoothed.values


def loess_smoothing(
    x: np.ndarray,
    y: np.ndarray,
    frac: float = 0.3,
    iterations: int = 1
) -> np.ndarray:
    """
    LOESS (Local Regression) smoothing.
    
    Args:
        x: Time points (equally spaced recommended)
        y: Observations
        frac: Fraction of data to use for local regression
        iterations: Number of robustness iterations
        
    Returns:
        Smoothed values
    """
    from statsmodels.nonparametric.smoothers_lowess import lowess
    
    if len(x) != len(y):
        raise ValueError("x and y must have same length")
    
    if frac <= 0 or frac > 1:
        raise ValueError("frac must be between 0 and 1")
    
    # LOESS smoothing
    smoothed = lowess(y, x, frac=frac, it=iterations, return_sorted=False)
    
    return smoothed


def detect_epidemic_threshold(
    counts: np.ndarray,
    method: str = "moving_average",
    window: int = 7,
    multiplier: float = 2.0
) -> Dict:
    """
    Detect epidemic threshold using various methods.
    
    Args:
        counts: Daily case counts
        method: Detection method
        window: Window size for baseline
        multiplier: Multiplier for threshold
        
    Returns:
        Dictionary with threshold and flags
    """
    counts = np.asarray(counts)
    
    if method == "moving_average":
        baseline = moving_average(counts, window=window)
        std = np.std(counts[:window]) if len(counts) >= window else np.std(counts)
        threshold = baseline + multiplier * std
    
    elif method == "percentile":
        baseline = np.percentile(counts, 75)
        threshold = baseline * multiplier
    
    elif method == "cumu_sum":
        # Cumulative sum method
        mean = np.mean(counts)
        std = np.std(counts)
        threshold = mean + multiplier * std
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Identify epidemic periods
    epidemic_flags = counts > threshold
    
    # Calculate epidemic metrics
    epidemic_days = np.sum(epidemic_flags)
    epidemic_periods = _find_contiguous_regions(epidemic_flags)
    
    return {
        "threshold": threshold,
        "baseline": baseline if method == "moving_average" else None,
        "epidemic_flags": epidemic_flags,
        "epidemic_days": epidemic_days,
        "epidemic_periods": epidemic_periods,
        "method": method
    }


def _find_contiguous_regions(flags: np.ndarray) -> List[Tuple[int, int]]:
    """Find contiguous True regions in boolean array."""
    regions = []
    start = None
    
    for i, flag in enumerate(flags):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            regions.append((start, i-1))
            start = None
    
    if start is not None:
        regions.append((start, len(flags)-1))
    
    return regions


def reproductive_number(
    incidence: np.ndarray,
    serial_interval: float = 5.0,
    method: str = "cori"
) -> np.ndarray:
    """
    Estimate time-varying reproductive number (R_t).
    
    Args:
        incidence: Daily incidence
        serial_interval: Mean serial interval in days
        method: Estimation method
        
    Returns:
        Estimated R_t over time
    """
    incidence = np.asarray(incidence, dtype=float)
    
    if method == "simple":
        # Simple moving average ratio
        window = int(serial_interval)
        if window < 1:
            window = 1
        
        # Pad with zeros for beginning
        padded = np.concatenate([np.zeros(window), incidence])
        
        R_t = np.zeros(len(incidence))
        for t in range(len(incidence)):
            numerator = np.sum(padded[t+1:t+window+1])
            denominator = np.sum(padded[t-window+1:t+1])
            
            if denominator > 0:
                R_t[t] = numerator / denominator
            else:
                R_t[t] = 0.0
    
    elif method == "cori":
        # Cori et al. method (simplified)
        # This is a simplified version
        R_t = np.zeros(len(incidence))
        for t in range(1, len(incidence)):
            if incidence[t-1] > 0:
                R_t[t] = incidence[t] / incidence[t-1]
            else:
                R_t[t] = 0.0
        
        # Smooth with serial interval
        R_t = moving_average(R_t, window=int(serial_interval))
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return R_t


def seasonality_decomposition(
    time_series: np.ndarray,
    period: int = 365,
    model: str = "additive"
) -> Dict[str, np.ndarray]:
    """
    Decompose time series into trend, seasonal, and residual components.
    
    Args:
        time_series: Time series data
        period: Seasonal period (e.g., 365 for daily annual)
        model: 'additive' or 'multiplicative'
        
    Returns:
        Dictionary with components
    """
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    # Ensure enough data points
    if len(time_series) < 2 * period:
        warnings.warn(f"Insufficient data for period {period}")
        period = min(period, len(time_series) // 2)
    
    # Create time index
    if isinstance(time_series, pd.Series):
        series = time_series
    else:
        series = pd.Series(time_series)
    
    # Perform decomposition
    result = seasonal_decompose(series, model=model, period=period, extrapolate_trend='freq')
    
    return {
        "observed": result.observed.values,
        "trend": result.trend.values,
        "seasonal": result.seasonal.values,
        "residual": result.resid.values,
        "period": period,
        "model": model
    }


def exponential_growth_rate(
    cases: np.ndarray,
    time_points: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Calculate exponential growth rate from case counts.
    
    Args:
        cases: Case counts over time
        time_points: Time points (optional)
        
    Returns:
        Dictionary with growth rate and doubling time
    """
    cases = np.asarray(cases, dtype=float)
    
    # Remove zeros for log transformation
    valid_mask = cases > 0
    if np.sum(valid_mask) < 2:
        return {"growth_rate": 0.0, "doubling_time": float('inf'), "r_squared": 0.0}
    
    cases_valid = cases[valid_mask]
    
    if time_points is None:
        time_points = np.arange(len(cases))[valid_mask]
    else:
        time_points = np.asarray(time_points)[valid_mask]
    
    # Linear regression on log cases
    log_cases = np.log(cases_valid)
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(time_points, log_cases)
    
    # Growth rate (per time unit)
    growth_rate = slope
    
    # Doubling time
    if growth_rate > 0:
        doubling_time = np.log(2) / growth_rate
    else:
        doubling_time = float('inf')
    
    return {
        "growth_rate": growth_rate,
        "doubling_time": doubling_time,
        "intercept": intercept,
        "r_squared": r_value**2,
        "p_value": p_value,
        "std_err": std_err
    }


def nowcasting(
    reported_cases: np.ndarray,
    delay_distribution: np.ndarray,
    method: str = "simple"
) -> np.ndarray:
    """
    Perform nowcasting to estimate true incidence accounting for reporting delays.
    
    Args:
        reported_cases: Cases reported by date of report
        delay_distribution: Probability distribution of reporting delays
        method: Nowcasting method
        
    Returns:
        Nowcasted incidence
    """
    reported_cases = np.asarray(reported_cases, dtype=float)
    delay_distribution = np.asarray(delay_distribution, dtype=float)
    
    # Normalize delay distribution
    delay_distribution = delay_distribution / np.sum(delay_distribution)
    
    n_days = len(reported_cases)
    n_delays = len(delay_distribution)
    
    if method == "simple":
        # Simple deconvolution
        nowcasted = np.zeros(n_days)
        
        for t in range(n_days):
            total = 0
            for d in range(min(n_delays, t + 1)):
                total += reported_cases[t - d] * delay_distribution[d]
            nowcasted[t] = total
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return nowcasted


def cumulative_curve(
    daily_cases: np.ndarray
) -> np.ndarray:
    """
    Calculate cumulative epidemic curve.
    
    Args:
        daily_cases: Daily new cases
        
    Returns:
        Cumulative cases
    """
    return np.cumsum(daily_cases)


def detect_peaks(
    time_series: np.ndarray,
    height: Optional[float] = None,
    distance: int = 7,
    prominence: Optional[float] = None
) -> Dict:
    """
    Detect peaks in time series data.
    
    Args:
        time_series: Time series data
        height: Minimum height of peaks
        distance: Minimum distance between peaks
        prominence: Minimum prominence of peaks
        
    Returns:
        Dictionary with peak indices and properties
    """
    peaks, properties = signal.find_peaks(
        time_series,
        height=height,
        distance=distance,
        prominence=prominence
    )
    
    return {
        "peak_indices": peaks,
        "peak_heights": properties.get('peak_heights', []),
        "prominences": properties.get('prominences', []),
        "left_bases": properties.get('left_bases', []),
        "right_bases": properties.get('right_bases', []),
        "n_peaks": len(peaks)
    }


#  MODULE EXPORTS 

__all__ = [
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
    'detect_peaks'
]
"""
This module provides cached calculator classes that optimize repeated
calculations and provide consistent interfaces for statistical computations.
"""

import numpy as np
from typing import Any, Dict, Optional, Union, Callable
from functools import lru_cache, wraps
import time
from dataclasses import dataclass
from enum import Enum


class CacheStrategy(Enum):
    """Caching strategies for calculators."""
    LRU = "lru"           # Least Recently Used
    MANUAL = "manual"     # Manual cache control
    NONE = "none"         # No caching


@dataclass
class CalculationStats:
    """Statistics about calculation performance."""
    call_count: int = 0
    cache_hits: int = 0
    total_time: float = 0.0
    last_call_time: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate as percentage."""
        if self.call_count == 0:
            return 0.0
        return (self.cache_hits / self.call_count) * 100
    
    @property
    def average_time(self) -> float:
        """Average calculation time in milliseconds."""
        if self.call_count == 0:
            return 0.0
        return (self.total_time / self.call_count) * 1000


class BaseCalculator:
    """
    Base class for all calculators with built-in caching and statistics.
    
    Features:
    - Automatic caching of results
    - Performance statistics
    - Input validation hooks
    - Consistent error handling
    """
    
    def __init__(self, cache_strategy: CacheStrategy = CacheStrategy.LRU):
        self.cache_strategy = cache_strategy
        self._cache: Dict[str, Any] = {}
        self.stats = CalculationStats()
        self._enabled = True
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            String cache key
        """
        # Convert args and kwargs to string representation
        args_str = ','.join(str(arg) for arg in args)
        kwargs_str = ','.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{args_str}|{kwargs_str}"
    
    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        self.stats = CalculationStats()
    
    def disable_cache(self) -> None:
        """Disable caching temporarily."""
        self._enabled = False
    
    def enable_cache(self) -> None:
        """Enable caching."""
        self._enabled = True
    
    def cached_method(self, func: Callable) -> Callable:
        """
        Decorator for caching method results (instance method usage).

        Usage: call on an instance, not on the class directly.
        For class-level decoration use @staticmethod + manual caching.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._enabled or self.cache_strategy == CacheStrategy.NONE:
                return func(*args, **kwargs)
            cache_key = self._generate_cache_key(*args[1:], **kwargs)
            self.stats.call_count += 1
            if cache_key in self._cache:
                self.stats.cache_hits += 1
                return self._cache[cache_key]
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            self.stats.total_time += (time.perf_counter() - start_time)
            if self.cache_strategy == CacheStrategy.LRU and len(self._cache) >= 1000:
                del self._cache[next(iter(self._cache))]
            self._cache[cache_key] = result
            return result
        return wrapper

    @staticmethod
    def _cache_decorator(func: Callable) -> Callable:
        """
        Class-level cache decorator using functools.lru_cache.
        Use this instead of @BaseCalculator.cached_method at class definition.
        """
        return lru_cache(maxsize=512)(func)


class EpidemiologicalCalculator(BaseCalculator):
    """
    Calculator for common epidemiological computations.
    
    Provides cached implementations of frequently used calculations.
    """
    
    def __init__(self, cache_strategy: CacheStrategy = CacheStrategy.LRU):
        super().__init__(cache_strategy)
    
    @lru_cache(maxsize=512)
    def risk_ratio(self, a: int, b: int, c: int, d: int) -> float:
        """
        Calculate risk ratio with caching.
        
        Args:
            a, b, c, d: 2x2 table cells
            
        Returns:
            Risk ratio
        """
        if (a + c) == 0 or (b + d) == 0:
            return float('nan')
        
        risk_exposed = a / (a + c)
        risk_unexposed = b / (b + d)
        
        if risk_unexposed == 0:
            return float('inf') if risk_exposed > 0 else float('nan')
        
        return risk_exposed / risk_unexposed
    
    @lru_cache(maxsize=512)
    def odds_ratio(self, a: int, b: int, c: int, d: int) -> float:
        """
        Calculate odds ratio with caching.
        
        Args:
            a, b, c, d: 2x2 table cells
            
        Returns:
            Odds ratio
        """
        if b == 0 or c == 0:
            return float('inf') if a * d > 0 else float('nan')
        
        return (a * d) / (b * c)
    
    @lru_cache(maxsize=512)
    def attributable_fraction_exposed(self, rr: float) -> float:
        """
        Calculate attributable fraction among exposed.
        
        Args:
            rr: Risk ratio
            
        Returns:
            Attributable fraction
        """
        if rr <= 0:
            return 0.0
        return (rr - 1) / rr
    
    @lru_cache(maxsize=512)
    def population_attributable_fraction(self, rr: float, p_exposed: float) -> float:
        """
        Calculate population attributable fraction.
        
        Args:
            rr: Risk ratio
            p_exposed: Proportion exposed in population
            
        Returns:
            Population attributable fraction
        """
        if rr <= 1 or p_exposed == 0:
            return 0.0
        
        numerator = p_exposed * (rr - 1)
        denominator = numerator + 1
        
        return numerator / denominator
    
    @lru_cache(maxsize=512)
    def standard_error_proportion(self, p: float, n: int) -> float:
        """
        Calculate standard error of a proportion.
        
        Args:
            p: Proportion (0-1)
            n: Sample size
            
        Returns:
            Standard error
        """
        if n <= 0:
            return float('nan')
        
        return np.sqrt(p * (1 - p) / n)
    
    @lru_cache(maxsize=512)
    def confidence_interval_proportion(
        self, 
        p: float, 
        n: int, 
        confidence: float = 0.95
    ) -> tuple:
        """
        Calculate confidence interval for proportion.
        
        Args:
            p: Proportion
            n: Sample size
            confidence: Confidence level (0-1)
            
        Returns:
            Tuple of (lower, upper)
        """
        from scipy import stats
        
        if n <= 0:
            return (float('nan'), float('nan'))
        
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        se = self.standard_error_proportion(p, n)
        margin = z * se
        
        lower = max(0, p - margin)
        upper = min(1, p + margin)
        
        return (lower, upper)
    
    @lru_cache(maxsize=512)
    def binomial_probability(
        self, 
        k: int, 
        n: int, 
        p: float
    ) -> float:
        """
        Calculate binomial probability P(X = k).
        
        Args:
            k: Number of successes
            n: Number of trials
            p: Probability of success
            
        Returns:
            Binomial probability
        """
        from scipy import stats
        return stats.binom.pmf(k, n, p)
    
    @lru_cache(maxsize=512)
    def poisson_probability(
        self, 
        k: int, 
        lambda_: float
    ) -> float:
        """
        Calculate Poisson probability P(X = k).
        
        Args:
            k: Number of events
            lambda_: Rate parameter
            
        Returns:
            Poisson probability
        """
        from scipy import stats
        return stats.poisson.pmf(k, lambda_)


class MatrixCalculator(BaseCalculator):
    """
    Calculator for matrix operations used in epidemiological models.
    """
    
    def __init__(self, cache_strategy: CacheStrategy = CacheStrategy.LRU):
        super().__init__(cache_strategy)
    
    @lru_cache(maxsize=512)
    def next_generation_matrix(
        self, 
        transmission_matrix: np.ndarray,
        duration_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Calculate next generation matrix R0 = K = T * D.
        
        Args:
            transmission_matrix: Matrix T
            duration_matrix: Matrix D
            
        Returns:
            Next generation matrix K
        """
        return transmission_matrix @ duration_matrix
    
    @lru_cache(maxsize=512)
    def basic_reproduction_number(
        self, 
        next_generation_matrix: np.ndarray
    ) -> float:
        """
        Calculate basic reproduction number R0.
        
        Args:
            next_generation_matrix: Matrix K
            
        Returns:
            R0 (spectral radius of K)
        """
        eigenvalues = np.linalg.eigvals(next_generation_matrix)
        return float(np.max(np.abs(eigenvalues)))
    
    @lru_cache(maxsize=512)
    def effective_reproduction_number(
        self, 
        R0: float, 
        susceptible_proportion: float
    ) -> float:
        """
        Calculate effective reproduction number Rt.
        
        Args:
            R0: Basic reproduction number
            susceptible_proportion: Proportion susceptible
            
        Returns:
            Effective reproduction number
        """
        return R0 * susceptible_proportion


# Singleton instances for common use
epi_calculator = EpidemiologicalCalculator()
matrix_calculator = MatrixCalculator()


def cached_function(maxsize: int = 128):
    """
    Decorator for caching function results.
    
    Args:
        maxsize: Maximum cache size
        
    Returns:
        Decorated function
    """
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = (args, tuple(sorted(kwargs.items())))
            
            if cache_key in cache:
                return cache[cache_key]
            
            result = func(*args, **kwargs)
            
            # Apply LRU eviction if needed
            if len(cache) >= maxsize:
                # Remove oldest entry
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            
            cache[cache_key] = result
            return result
        
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    return decorator
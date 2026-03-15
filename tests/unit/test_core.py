"""
tests/unit/test_core.py
Unit tests for epitools.core.calculator, core.validator, core.exceptions
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
import pytest

from epitools.core.calculator import (
    BaseCalculator, CalculationStats, CacheStrategy,
    EpidemiologicalCalculator, MatrixCalculator,
    cached_function, epi_calculator, matrix_calculator,
)
from epitools.core.validator import (
    ValidationError,
    check_convergence, validate_2x2_table, validate_binary_variable,
    validate_confidence_level, validate_dataframe, validate_numeric_array,
    validate_positive, validate_proportion, validate_sample_size,
)
from epitools.core.exceptions import (
    EpiToolsError, ConvergenceError, ConfigurationError, DataError,
    ModelError, StatisticalError, DimensionError, ParameterError,
    ComputationError, FileError, PlotError,
)



# 1. CacheStrategy

class TestCacheStrategy:
    def test_lru_value(self):        assert CacheStrategy.LRU.value    == "lru"
    def test_manual_value(self):     assert CacheStrategy.MANUAL.value == "manual"
    def test_none_value(self):       assert CacheStrategy.NONE.value   == "none"
    def test_enum_members(self):
        assert {s.value for s in CacheStrategy} == {"lru", "manual", "none"}



# 2. CalculationStats

class TestCalculationStats:
    def test_defaults(self):
        s = CalculationStats()
        assert s.call_count == 0 and s.cache_hits == 0
        assert s.total_time == 0.0 and s.last_call_time == 0.0

    def test_hit_rate_zero_calls(self):   assert CalculationStats().cache_hit_rate == 0.0
    def test_hit_rate_partial(self):
        assert CalculationStats(call_count=10, cache_hits=4).cache_hit_rate == pytest.approx(40.0)
    def test_hit_rate_100(self):
        assert CalculationStats(call_count=5, cache_hits=5).cache_hit_rate == pytest.approx(100.0)
    def test_avg_time_zero(self):         assert CalculationStats().average_time == 0.0
    def test_avg_time_ms(self):
        # total_time seconds → average_time milliseconds
        assert CalculationStats(call_count=4, total_time=0.004).average_time == pytest.approx(1.0)



# 3. BaseCalculator

class TestBaseCalculator:
    def test_default_strategy(self):
        assert BaseCalculator().cache_strategy == CacheStrategy.LRU
    def test_custom_strategy(self):
        assert BaseCalculator(CacheStrategy.NONE).cache_strategy == CacheStrategy.NONE
    def test_cache_empty_on_init(self):   assert BaseCalculator()._cache == {}
    def test_enabled_on_init(self):       assert BaseCalculator()._enabled is True
    def test_stats_fresh(self):           assert BaseCalculator().stats.call_count == 0

    def test_cache_key_positional(self):
        assert BaseCalculator()._generate_cache_key(1, 2) == "1,2|"
    def test_cache_key_kwargs(self):
        k = BaseCalculator()._generate_cache_key(a=1, b=2)
        assert "a=1" in k and "b=2" in k
    def test_cache_key_same_args_equal(self):
        c = BaseCalculator()
        assert c._generate_cache_key(1, x=2) == c._generate_cache_key(1, x=2)
    def test_cache_key_different_args_differ(self):
        c = BaseCalculator()
        assert c._generate_cache_key(1, 2) != c._generate_cache_key(1, 3)

    def test_clear_cache(self):
        c = BaseCalculator()
        c._cache["k"] = "v"; c.stats.call_count = 5
        c.clear_cache()
        assert c._cache == {} and c.stats.call_count == 0

    def test_disable_enable(self):
        c = BaseCalculator()
        c.disable_cache(); assert c._enabled is False
        c.enable_cache();  assert c._enabled is True

    def test_cached_method_stores(self):
        c = BaseCalculator()
        wrapped = c.cached_method(lambda self_, x: x * 2)
        assert wrapped(c, 5) == 10
        assert len(c._cache) == 1

    def test_cached_method_second_call_from_cache(self):
        c = BaseCalculator(); calls = [0]
        def fn(self_, x): calls[0] += 1; return x
        w = c.cached_method(fn)
        w(c, 7); w(c, 7)
        assert calls[0] == 1 and c.stats.cache_hits == 1

    def test_cached_method_disabled(self):
        c = BaseCalculator(); c.disable_cache(); calls = [0]
        def fn(self_, x): calls[0] += 1; return x
        w = c.cached_method(fn)
        w(c, 3); w(c, 3)
        assert calls[0] == 2 and len(c._cache) == 0

    def test_cached_method_none_strategy(self):
        c = BaseCalculator(CacheStrategy.NONE); calls = [0]
        def fn(self_, x): calls[0] += 1; return x
        w = c.cached_method(fn)
        w(c, 1); w(c, 1)
        assert calls[0] == 2

    def test_call_count_updated(self):
        c = BaseCalculator()
        w = c.cached_method(lambda self_, x: x)
        w(c, 1); w(c, 2); w(c, 1)   # 3 calls, 1 hit
        assert c.stats.call_count == 3 and c.stats.cache_hits == 1

    def test_lru_eviction(self):
        c = BaseCalculator()
        w = c.cached_method(lambda self_, x: x)
        for i in range(1002): w(c, i)
        assert len(c._cache) <= 1000



# 4. EpidemiologicalCalculator

@pytest.fixture
def ecalc():
    return EpidemiologicalCalculator()


class TestRiskRatio:
    def test_nominal(self, ecalc):
        assert ecalc.risk_ratio(40, 10, 20, 30) == pytest.approx(2.667, rel=1e-3)
    def test_equal_risks(self, ecalc):
        assert ecalc.risk_ratio(10, 10, 10, 10) == pytest.approx(1.0)
    def test_zero_exposed_cases(self, ecalc):
        assert ecalc.risk_ratio(0, 10, 10, 10) == pytest.approx(0.0)
    def test_zero_unexposed_risk(self, ecalc):
        # b=0, d=0 → b+d=0 → undefined denominator group → nan (not inf)
        assert math.isnan(ecalc.risk_ratio(10, 0, 5, 0))
    def test_zero_unexposed_with_controls(self, ecalc):
        # b=0 but d>0 → unexposed risk=0 → RR = inf
        assert math.isinf(ecalc.risk_ratio(10, 0, 5, 5))
    def test_empty_row_nan(self, ecalc):
        assert math.isnan(ecalc.risk_ratio(0, 5, 0, 5))
    def test_higher_exposed_risk(self, ecalc):
        assert ecalc.risk_ratio(30, 10, 10, 30) > 1.0


class TestOddsRatio:
    def test_nominal(self, ecalc):
        assert ecalc.odds_ratio(40, 10, 20, 30) == pytest.approx(6.0)
    def test_equal(self, ecalc):
        assert ecalc.odds_ratio(10, 10, 10, 10) == pytest.approx(1.0)
    def test_zero_b_inf(self, ecalc):
        assert math.isinf(ecalc.odds_ratio(10, 0, 5, 10))
    def test_zero_c_inf(self, ecalc):
        assert math.isinf(ecalc.odds_ratio(10, 5, 0, 10))
    def test_reciprocal_symmetry(self, ecalc):
        or1 = ecalc.odds_ratio(40, 10, 20, 30)
        or2 = ecalc.odds_ratio(10, 40, 30, 20)
        assert or1 == pytest.approx(1.0 / or2, rel=1e-6)


class TestAttributableFraction:
    def test_af_exposed(self, ecalc):
        assert ecalc.attributable_fraction_exposed(2.0) == pytest.approx(0.5)
    def test_af_rr_one(self, ecalc):
        assert ecalc.attributable_fraction_exposed(1.0) == pytest.approx(0.0)
    def test_af_rr_zero(self, ecalc):
        assert ecalc.attributable_fraction_exposed(0.0) == pytest.approx(0.0)
    def test_af_rr_negative(self, ecalc):
        assert ecalc.attributable_fraction_exposed(-1.0) == pytest.approx(0.0)
    def test_af_large_rr(self, ecalc):
        assert ecalc.attributable_fraction_exposed(10.0) == pytest.approx(0.9)

    def test_paf_nominal(self, ecalc):
        # PAF = 0.5*(2-1)/(0.5*(2-1)+1) = 0.5/1.5 = 1/3
        assert ecalc.population_attributable_fraction(2.0, 0.5) == pytest.approx(1/3, rel=1e-3)
    def test_paf_rr_one(self, ecalc):
        assert ecalc.population_attributable_fraction(1.0, 0.5) == pytest.approx(0.0)
    def test_paf_zero_exposed(self, ecalc):
        assert ecalc.population_attributable_fraction(3.0, 0.0) == pytest.approx(0.0)
    def test_paf_bounded(self, ecalc):
        paf = ecalc.population_attributable_fraction(4.0, 0.3)
        assert 0 < paf < 1


class TestStandardError:
    def test_se_proportion(self, ecalc):
        assert ecalc.standard_error_proportion(0.5, 100) == pytest.approx(0.05)
    def test_se_zero_n(self, ecalc):
        assert math.isnan(ecalc.standard_error_proportion(0.5, 0))
    def test_se_negative_n(self, ecalc):
        assert math.isnan(ecalc.standard_error_proportion(0.5, -1))
    def test_se_p_zero(self, ecalc):
        assert ecalc.standard_error_proportion(0.0, 100) == pytest.approx(0.0)


class TestConfidenceIntervalProportion:
    def test_contains_proportion(self, ecalc):
        lo, hi = ecalc.confidence_interval_proportion(0.5, 100)
        assert lo < 0.5 < hi
    def test_bounds_0_to_1(self, ecalc):
        lo, hi = ecalc.confidence_interval_proportion(0.5, 100)
        assert 0 <= lo and hi <= 1
    def test_zero_n_nan(self, ecalc):
        lo, hi = ecalc.confidence_interval_proportion(0.5, 0)
        assert math.isnan(lo) and math.isnan(hi)
    def test_larger_n_narrower(self, ecalc):
        lo1, hi1 = ecalc.confidence_interval_proportion(0.3, 50)
        lo2, hi2 = ecalc.confidence_interval_proportion(0.3, 500)
        assert (hi1 - lo1) > (hi2 - lo2)
    def test_99_wider_than_95(self, ecalc):
        lo95, hi95 = ecalc.confidence_interval_proportion(0.5, 100, 0.95)
        lo99, hi99 = ecalc.confidence_interval_proportion(0.5, 100, 0.99)
        assert (hi99 - lo99) > (hi95 - lo95)


class TestProbabilities:
    def test_binomial_nominal(self, ecalc):
        assert ecalc.binomial_probability(5, 10, 0.5) == pytest.approx(0.2461, rel=1e-3)
    def test_binomial_sums_to_one(self, ecalc):
        assert sum(ecalc.binomial_probability(k, 5, 0.4) for k in range(6)) == pytest.approx(1.0)
    def test_binomial_peak_at_mode(self, ecalc):
        probs = [ecalc.binomial_probability(k, 10, 0.5) for k in range(11)]
        assert probs[5] == max(probs)
    def test_poisson_nominal(self, ecalc):
        assert ecalc.poisson_probability(3, 3.0) == pytest.approx(0.2240, rel=1e-3)
    def test_poisson_zero_k(self, ecalc):
        assert ecalc.poisson_probability(0, 2.0) == pytest.approx(math.exp(-2), rel=1e-6)
    def test_poisson_range(self, ecalc):
        assert 0 <= ecalc.poisson_probability(5, 4.0) <= 1



# 5. MatrixCalculator

class TestMatrixCalculator:
    @pytest.fixture
    def mc(self): return MatrixCalculator()

    def test_effective_rt(self, mc):
        assert mc.effective_reproduction_number(4.0, 0.5) == pytest.approx(2.0)
    def test_effective_rt_full(self, mc):
        assert mc.effective_reproduction_number(3.0, 1.0) == pytest.approx(3.0)
    def test_effective_rt_zero(self, mc):
        assert mc.effective_reproduction_number(3.0, 0.0) == pytest.approx(0.0)
    def test_basic_r0(self, mc):
        K = np.array([[2.0, 0.0],[0.0, 1.0]])
        assert mc.basic_reproduction_number(K) == pytest.approx(2.0)
    def test_basic_r0_identity(self, mc):
        assert mc.basic_reproduction_number(np.eye(3)) == pytest.approx(1.0)
    def test_ngm(self, mc):
        T = np.array([[1.0, 0.0],[0.0, 2.0]])
        D = np.array([[3.0, 0.0],[0.0, 4.0]])
        np.testing.assert_array_almost_equal(mc.next_generation_matrix(T, D),
                                              np.array([[3.0, 0.0],[0.0, 8.0]]))



# 6. Singletons & cached_function

class TestSingletons:
    def test_types(self):
        assert isinstance(epi_calculator, EpidemiologicalCalculator)
        assert isinstance(matrix_calculator, MatrixCalculator)
    def test_epi_works(self):
        assert epi_calculator.risk_ratio(10, 5, 5, 10) > 0
    def test_matrix_works(self):
        assert matrix_calculator.effective_reproduction_number(3.0, 0.8) == pytest.approx(2.4)

class TestCachedFunction:
    def test_caches(self):
        calls = [0]
        @cached_function(maxsize=10)
        def fn(x): calls[0] += 1; return x * 2
        fn(5); fn(5)
        assert calls[0] == 1

    def test_different_args(self):
        calls = [0]
        @cached_function(maxsize=10)
        def fn(x): calls[0] += 1; return x
        fn(1); fn(2)
        assert calls[0] == 2

    def test_clear_cache(self):
        calls = [0]
        @cached_function(maxsize=10)
        def fn(x): calls[0] += 1; return x
        fn(1); fn.clear_cache(); fn(1)
        assert calls[0] == 2

    def test_eviction(self):
        @cached_function(maxsize=3)
        def fn(x): return x
        for i in range(5): fn(i)  # should not raise

    def test_correct_value(self):
        @cached_function(maxsize=10)
        def sq(x): return x ** 2
        assert sq(7) == 49 and sq(7) == 49



# 7. validate_2x2_table

class TestValidate2x2Table:
    def test_nominal(self):
        assert validate_2x2_table(40, 10, 20, 30) == (40, 10, 20, 30)
    def test_returns_tuple(self):
        assert isinstance(validate_2x2_table(1, 2, 3, 4), tuple)
    def test_float_coerced(self):
        a, b, c, d = validate_2x2_table(40.0, 10.0, 20.0, 30.0)
        assert all(isinstance(v, int) for v in [a, b, c, d])
    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            validate_2x2_table(-1, 10, 20, 30)
    def test_zeros_allowed_default(self):
        assert validate_2x2_table(0, 0, 0, 0) == (0, 0, 0, 0)
    def test_zero_not_allowed(self):
        with pytest.raises(ValidationError, match="zero"):
            validate_2x2_table(0, 10, 20, 30, allow_zero=False)
    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError):
            validate_2x2_table("x", 10, 20, 30)
    def test_string_number_coerced(self):
        a, *_ = validate_2x2_table("40", 10, 20, 30)
        assert a == 40



# 8. validate_proportion

class TestValidateProportion:
    def test_valid(self):         assert validate_proportion(0.5) == pytest.approx(0.5)
    def test_zero_allowed(self):  assert validate_proportion(0.0) == pytest.approx(0.0)
    def test_one_allowed(self):   assert validate_proportion(1.0) == pytest.approx(1.0)
    def test_above_one(self):
        with pytest.raises(ValidationError): validate_proportion(1.1)
    def test_below_zero(self):
        with pytest.raises(ValidationError): validate_proportion(-0.1)
    def test_zero_not_at_boundary(self):
        with pytest.raises(ValidationError): validate_proportion(0.0, allow_boundary=False)
    def test_one_not_at_boundary(self):
        with pytest.raises(ValidationError): validate_proportion(1.0, allow_boundary=False)
    def test_non_numeric(self):
        with pytest.raises(ValidationError): validate_proportion("high")
    def test_name_in_error(self):
        with pytest.raises(ValidationError, match="my_p"): validate_proportion(2.0, name="my_p")



# 9. validate_confidence_level

class TestValidateConfidenceLevel:
    def test_95(self):   assert validate_confidence_level(0.95) == pytest.approx(0.95)
    def test_zero(self):
        with pytest.raises(ValidationError): validate_confidence_level(0.0)
    def test_one(self):
        with pytest.raises(ValidationError): validate_confidence_level(1.0)
    def test_non_numeric(self):
        with pytest.raises(ValidationError): validate_confidence_level("high")
    def test_string_coerced(self):
        assert validate_confidence_level("0.95") == pytest.approx(0.95)



# 10. validate_sample_size

class TestValidateSampleSize:
    def test_valid(self):          assert validate_sample_size(100) == 100
    def test_returns_int(self):    assert isinstance(validate_sample_size(100), int)
    def test_float_coerced(self):  assert validate_sample_size(100.9) == 100
    def test_zero_raises(self):
        with pytest.raises(ValidationError): validate_sample_size(0)
    def test_negative_raises(self):
        with pytest.raises(ValidationError): validate_sample_size(-5)
    def test_custom_min(self):     assert validate_sample_size(30, min_size=30) == 30
    def test_below_min(self):
        with pytest.raises(ValidationError): validate_sample_size(29, min_size=30)
    def test_non_numeric(self):
        with pytest.raises(ValidationError): validate_sample_size("big")



# 11. validate_dataframe

class TestValidateDataframe:
    def _df(self, rows=5, cols=None):
        return pd.DataFrame({c: range(rows) for c in (cols or ["a","b","c"])})

    def test_valid(self):
        assert isinstance(validate_dataframe(self._df()), pd.DataFrame)
    def test_not_df_raises(self):
        with pytest.raises(ValidationError): validate_dataframe([[1,2],[3,4]])
    def test_too_few_rows(self):
        with pytest.raises(ValidationError, match="rows"):
            validate_dataframe(self._df(2), min_rows=5)
    def test_missing_column(self):
        with pytest.raises(ValidationError, match="Missing"):
            validate_dataframe(self._df(cols=["a","b"]), required_columns=["a","b","x"])
    def test_nan_not_allowed(self):
        with pytest.raises(ValidationError, match="NaN"):
            validate_dataframe(pd.DataFrame({"a":[1,None,3]}), allow_nan=False)
    def test_nan_allowed(self):
        result = validate_dataframe(pd.DataFrame({"a":[1,None,3]}), allow_nan=True)
        assert result is not None



# 12. validate_binary_variable

class TestValidateBinaryVariable:
    def test_0_1_ints(self):
        assert isinstance(validate_binary_variable([0,1,0,1]), pd.Series)
    def test_booleans(self):
        assert isinstance(validate_binary_variable([True, False, True]), pd.Series)
    def test_invalid_values(self):
        with pytest.raises(ValidationError, match="binary"):
            validate_binary_variable([0, 1, 2])
    def test_strings_raise(self):
        with pytest.raises(ValidationError, match="binary"):
            validate_binary_variable(["yes","no"])
    def test_numpy_array(self):
        assert isinstance(validate_binary_variable(np.array([0,1,0,1])), pd.Series)
    def test_pandas_series(self):
        assert isinstance(validate_binary_variable(pd.Series([0,1,1,0])), pd.Series)
    def test_not_array_like(self):
        with pytest.raises(ValidationError): validate_binary_variable(42)



# 13. validate_numeric_array

class TestValidateNumericArray:
    def test_valid(self):
        assert isinstance(validate_numeric_array([1.0, 2.0, 3.0]), np.ndarray)
    def test_nan_not_allowed(self):
        with pytest.raises(ValidationError, match="NaN"):
            validate_numeric_array([1.0, float("nan")])
    def test_nan_allowed(self):
        arr = validate_numeric_array([1.0, float("nan")], allow_nan=True)
        assert np.isnan(arr[1])
    def test_inf_not_allowed(self):
        with pytest.raises(ValidationError, match="Infinite"):
            validate_numeric_array([1.0, float("inf")])
    def test_inf_allowed(self):
        arr = validate_numeric_array([1.0, float("inf")], allow_inf=True)
        assert np.isinf(arr[1])
    def test_too_short(self):
        with pytest.raises(ValidationError, match="elements"):
            validate_numeric_array([1.0], min_length=5)
    def test_non_numeric(self):
        with pytest.raises(ValidationError):
            validate_numeric_array(["a","b","c"])
    def test_dtype_float(self):
        assert validate_numeric_array([1,2,3]).dtype == float



# 14. validate_positive

class TestValidatePositive:
    def test_valid(self):            assert validate_positive(5.0) == pytest.approx(5.0)
    def test_zero_strict_raises(self):
        with pytest.raises(ValidationError, match="positive"):
            validate_positive(0.0, strict=True)
    def test_zero_non_strict(self):  assert validate_positive(0.0, strict=False) == pytest.approx(0.0)
    def test_negative_raises(self):
        with pytest.raises(ValidationError): validate_positive(-1.0)
    def test_non_numeric(self):
        with pytest.raises(ValidationError): validate_positive("big")
    def test_name_in_error(self):
        with pytest.raises(ValidationError, match="beta"):
            validate_positive(-0.5, name="beta")



# 15. check_convergence

class TestCheckConvergence:
    def test_converged(self):
        assert check_convergence(np.array([1.0, 2.0]), iteration=5) is True
    def test_max_iterations(self):
        with pytest.raises(ValidationError, match="converge"):
            check_convergence(np.array([1.0]), max_iterations=10, iteration=10)
    def test_nan_false(self):
        assert check_convergence(np.array([1.0, float("nan")]), iteration=0) is False
    def test_inf_false(self):
        assert check_convergence(np.array([1.0, float("inf")]), iteration=0) is False
    def test_just_below_max(self):
        assert check_convergence(np.array([1.0]), max_iterations=10, iteration=9) is True
    def test_zeros(self):
        assert check_convergence(np.zeros(5), iteration=1) is True



# 16. Exceptions

class TestExceptions:
    def test_base_raises(self):
        with pytest.raises(EpiToolsError): raise EpiToolsError("test")

    def test_default_message(self):
        assert len(EpiToolsError().message) > 0

    def test_custom_message(self):
        assert EpiToolsError("hello").message == "hello"

    @pytest.mark.parametrize("cls", [
        ConvergenceError, ConfigurationError, DataError, ModelError,
        StatisticalError, DimensionError, ParameterError,
        ComputationError, FileError, PlotError,
    ])
    def test_inherits_epitools_error(self, cls):
        assert isinstance(cls(), EpiToolsError)
        assert isinstance(cls(), Exception)

    @pytest.mark.parametrize("cls", [
        ConvergenceError, ConfigurationError, DataError, ModelError,
        StatisticalError, DimensionError, ParameterError,
        ComputationError, FileError, PlotError,
    ])
    def test_catchable_as_base(self, cls):
        with pytest.raises(EpiToolsError): raise cls("test")

    def test_validator_validation_error_is_value_error(self):
        from epitools.core.validator import ValidationError as VE
        with pytest.raises(ValueError): raise VE("bad value")

    def test_exceptions_validation_error_is_epitools_error(self):
        from epitools.core.exceptions import ValidationError as EVE
        with pytest.raises(EpiToolsError): raise EVE("bad value")
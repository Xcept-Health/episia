"""
tests/unit/test_utilities_coverage.py

Targeted tests to increase coverage of core/utilities.py (50% -> ~80%).
"""
import warnings
import pytest
import numpy as np


#  validate_input decorator 

class TestValidateInput:

    def test_general_validator_applied(self):
        from episia.core.utilities import validate_input
        @validate_input(validator=lambda x: x)
        def identity(a, b):
            return a + b
        assert identity(1, 2) == 3

    def test_named_validator_applied(self):
        from episia.core.utilities import validate_input
        @validate_input(x=lambda v: abs(v))
        def func(x):
            return x
        assert func(-5) == 5

    def test_default_args_applied(self):
        from episia.core.utilities import validate_input
        @validate_input(x=lambda v: v * 2)
        def func(x=3):
            return x
        assert func() == 6


#  deprecated decorator 

class TestDeprecated:

    def test_emits_deprecation_warning(self):
        from episia.core.utilities import deprecated
        @deprecated("0.1.0")
        def old_func():
            return 42
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_func()
        assert result == 42
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    def test_warning_contains_version(self):
        from episia.core.utilities import deprecated
        @deprecated("0.2.0", replacement="new_func")
        def old_func():
            pass
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_func()
        assert "0.2.0" in str(w[0].message)

    def test_warning_contains_replacement(self):
        from episia.core.utilities import deprecated
        @deprecated("0.2.0", replacement="new_func")
        def old_func():
            pass
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_func()
        assert "new_func" in str(w[0].message)


#  memoize decorator 

class TestMemoize:

    def test_returns_correct_value(self):
        from episia.core.utilities import memoize
        @memoize()
        def square(x):
            return x * x
        assert square(4) == 16

    def test_caches_result(self):
        from episia.core.utilities import memoize
        call_count = [0]
        @memoize()
        def expensive(x):
            call_count[0] += 1
            return x * 2
        expensive(5)
        expensive(5)
        assert call_count[0] == 1

    def test_different_args_not_cached(self):
        from episia.core.utilities import memoize
        @memoize()
        def func(x):
            return x
        assert func(1) == 1
        assert func(2) == 2

    def test_cache_size_limit(self):
        from episia.core.utilities import memoize
        @memoize(maxsize=3)
        def func(x):
            return x
        for i in range(5):
            func(i)  # should not raise

    def test_clear_cache(self):
        from episia.core.utilities import memoize
        call_count = [0]
        @memoize()
        def func(x):
            call_count[0] += 1
            return x
        func(1)
        func.clear_cache()
        func(1)
        assert call_count[0] == 2


#  safe_divide 

class TestSafeDivide:

    def test_normal_division(self):
        from episia.core.utilities import safe_divide
        assert safe_divide(10, 2) == 5.0

    def test_zero_denominator_returns_default(self):
        from episia.core.utilities import safe_divide
        assert safe_divide(10, 0) == 0.0

    def test_custom_default(self):
        from episia.core.utilities import safe_divide
        assert safe_divide(10, 0, default=-1) == -1

    def test_numpy_array(self):
        from episia.core.utilities import safe_divide
        num = np.array([10.0, 20.0, 30.0])
        den = np.array([2.0, 0.0, 5.0])
        result = safe_divide(num, den)
        assert result[0] == 5.0
        assert result[1] == 0.0
        assert result[2] == 6.0


#  clip_values 

class TestClipValues:

    def test_scalar_clipped_lower(self):
        from episia.core.utilities import clip_values
        assert clip_values(-5, lower=0) == 0

    def test_scalar_clipped_upper(self):
        from episia.core.utilities import clip_values
        assert clip_values(15, upper=10) == 10

    def test_scalar_no_clip(self):
        from episia.core.utilities import clip_values
        assert clip_values(5, lower=0, upper=10) == 5

    def test_array_clipped(self):
        from episia.core.utilities import clip_values
        arr = np.array([-1.0, 5.0, 15.0])
        result = clip_values(arr, lower=0, upper=10)
        np.testing.assert_array_equal(result, [0.0, 5.0, 10.0])


#  format_number 

class TestFormatNumber:

    def test_normal_float(self):
        from episia.core.utilities import format_number
        assert format_number(3.14159, decimals=2) == "3.14"

    def test_nan_returns_nan_string(self):
        from episia.core.utilities import format_number
        assert format_number(float("nan")) == "NaN"

    def test_inf_returns_inf_string(self):
        from episia.core.utilities import format_number
        assert format_number(float("inf")) == "Inf"

    def test_neg_inf(self):
        from episia.core.utilities import format_number
        assert format_number(float("-inf")) == "-Inf"

    def test_scientific_notation(self):
        from episia.core.utilities import format_number
        result = format_number(0.000123, scientific=True)
        assert "e" in result.lower()


#  format_pvalue 

class TestFormatPvalue:

    def test_very_small(self):
        from episia.core.utilities import format_pvalue
        assert format_pvalue(0.0001) == "<0.001"

    def test_very_large(self):
        from episia.core.utilities import format_pvalue
        assert format_pvalue(0.9995) == ">0.999"

    def test_normal_value(self):
        from episia.core.utilities import format_pvalue
        assert format_pvalue(0.045) == "0.045"


#  create_bins 

class TestCreateBins:

    def test_equal_width(self):
        from episia.core.utilities import create_bins
        data = np.arange(100, dtype=float)
        bins = create_bins(data, n_bins=10, method="equal_width")
        assert len(bins) == 11

    def test_equal_frequency(self):
        from episia.core.utilities import create_bins
        data = np.arange(100, dtype=float)
        bins = create_bins(data, n_bins=5, method="equal_frequency")
        assert len(bins) == 6

    def test_unknown_method_raises(self):
        from episia.core.utilities import create_bins
        with pytest.raises(ValueError):
            create_bins(np.arange(10, dtype=float), method="invalid")


#  logit / expit 

class TestLogitExpit:

    def test_logit_0_5(self):
        from episia.core.utilities import logit
        assert logit(0.5) == pytest.approx(0.0, abs=1e-6)

    def test_expit_0(self):
        from episia.core.utilities import expit
        assert expit(0.0) == pytest.approx(0.5, abs=1e-6)

    def test_logit_expit_inverse(self):
        from episia.core.utilities import logit, expit
        p = 0.3
        assert expit(logit(p)) == pytest.approx(p, abs=1e-6)


#  standardize 

class TestStandardize:

    def test_mean_zero(self):
        from episia.core.utilities import standardize
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize(data)
        assert np.mean(result) == pytest.approx(0.0, abs=1e-10)

    def test_std_one(self):
        from episia.core.utilities import standardize
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = standardize(data)
        assert np.std(result) == pytest.approx(1.0, abs=1e-6)


#  winsorize 

class TestWinsorize:

    def test_clips_outliers(self):
        from episia.core.utilities import winsorize
        data = np.array([1.0, 2.0, 3.0, 100.0])
        result = winsorize(data, lower=0.0, upper=0.9)
        assert result[-1] < 100.0

    def test_shape_preserved(self):
        from episia.core.utilities import winsorize
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = winsorize(data)
        assert len(result) == len(data)


#  numpy_errstate context manager 

class TestNumpyErrstate:

    def test_restores_state(self):
        from episia.core.utilities import numpy_errstate
        old = np.geterr()["divide"]
        with numpy_errstate(divide="ignore"):
            _ = np.array([1.0]) / np.array([0.0])
        assert np.geterr()["divide"] == old


#  type checking 

class TestTypeChecking:

    def test_is_numeric_int(self):
        from episia.core.utilities import is_numeric
        assert is_numeric(42) is True

    def test_is_numeric_float(self):
        from episia.core.utilities import is_numeric
        assert is_numeric(3.14) is True

    def test_is_numeric_string(self):
        from episia.core.utilities import is_numeric
        assert is_numeric("hello") is False

    def test_is_integer_array_true(self):
        from episia.core.utilities import is_integer_array
        assert is_integer_array(np.array([1, 2, 3])) is True

    def test_is_integer_array_false(self):
        from episia.core.utilities import is_integer_array
        assert is_integer_array(np.array([1.5, 2.0])) is False

    def test_is_binary_array_true(self):
        from episia.core.utilities import is_binary_array
        assert is_binary_array(np.array([0, 1, 0, 1])) is True

    def test_is_binary_array_false(self):
        from episia.core.utilities import is_binary_array
        assert is_binary_array(np.array([0, 1, 2])) is False


#  sanitize_filename 

class TestSanitizeFilename:

    def test_removes_invalid_chars(self):
        from episia.core.utilities import sanitize_filename
        result = sanitize_filename("file<>name.txt")
        assert "<" not in result
        assert ">" not in result

    def test_normal_filename_unchanged(self):
        from episia.core.utilities import sanitize_filename
        assert sanitize_filename("report_2024.pdf") == "report_2024.pdf"


#  set_random_seed / generate_random_id 

class TestRandomUtils:

    def test_set_seed_reproducibility(self):
        from episia.core.utilities import set_random_seed
        set_random_seed(42)
        a = np.random.rand()
        set_random_seed(42)
        b = np.random.rand()
        assert a == b

    def test_set_seed_none_no_error(self):
        from episia.core.utilities import set_random_seed
        set_random_seed(None)  # should not raise

    def test_generate_random_id_length(self):
        from episia.core.utilities import generate_random_id
        assert len(generate_random_id(10)) == 10

    def test_generate_random_id_default(self):
        from episia.core.utilities import generate_random_id
        assert len(generate_random_id()) == 8

    def test_generate_random_id_unique(self):
        from episia.core.utilities import generate_random_id
        ids = {generate_random_id() for _ in range(100)}
        assert len(ids) > 90  # quasi-unique
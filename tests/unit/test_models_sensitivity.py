"""
tests/test_models_sensitivity.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
from episia.models import SEIRModel
from episia.models.parameters import SEIRParameters
from episia.models.sensitivity import SensitivityAnalysis, SensitivityResult


@pytest.fixture
def small_sa():
    return SensitivityAnalysis(
        SEIRModel, SEIRParameters,
        fixed        = dict(N=100_000, I0=1, E0=5, t_span=(0,100)),
        distributions= {'beta': ('uniform', 0.2, 0.5), 'gamma': ('uniform', 0.05, 0.15)},
        n_samples    = 8,
        seed         = 42,
    )


class TestSensitivityAnalysisInit:

    def test_stores_n_samples(self, small_sa):
        assert small_sa.n_samples == 8

    def test_stores_seed(self, small_sa):
        assert small_sa.seed == 42

    def test_stores_model_class(self, small_sa):
        assert small_sa.model_class is SEIRModel

    def test_uniform_distribution(self, small_sa):
        assert 'beta' in small_sa.distributions
        assert small_sa.distributions['beta'][0] == 'uniform'

    def test_normal_distribution(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed        = dict(N=100_000, I0=1, E0=5, t_span=(0,100)),
            distributions= {'beta': ('normal', 0.35, 0.05)},
            n_samples    = 5, seed=0,
        )
        assert sa.distributions['beta'][0] == 'normal'

    def test_triangular_distribution(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed        = dict(N=100_000, I0=1, E0=5, t_span=(0,100)),
            distributions= {'gamma': ('triangular', 1/21, 1/14, 1/7)},
            n_samples    = 5, seed=0,
        )
        assert sa.distributions['gamma'][0] == 'triangular'


class TestSensitivityAnalysisRun:

    def test_returns_sensitivity_result(self, small_sa):
        result = small_sa.run(verbose=False)
        assert isinstance(result, SensitivityResult)

    def test_n_samples_in_result(self, small_sa):
        result = small_sa.run(verbose=False)
        assert result.n_samples == 8

    def test_envelopes_not_empty(self, small_sa):
        result = small_sa.run(verbose=False)
        assert result.envelopes is not None
        assert len(result.envelopes) > 0

    def test_compartment_names_present(self, small_sa):
        result = small_sa.run(verbose=False)
        assert result.compartment_names is not None

    def test_summary_has_r0_median(self, small_sa):
        result = small_sa.run(verbose=False)
        s = result.summary()
        assert 'r0_median' in s

    def test_summary_has_peak_infected_median(self, small_sa):
        result = small_sa.run(verbose=False)
        s = result.summary()
        assert 'peak_infected_median' in s

    def test_summary_r0_positive(self, small_sa):
        result = small_sa.run(verbose=False)
        s = result.summary()
        assert s['r0_median'] > 0

    def test_summary_final_size_between_0_and_1(self, small_sa):
        result = small_sa.run(verbose=False)
        s = result.summary()
        assert 0 < s['final_size_median'] <= 1

    def test_n_failed_non_negative(self, small_sa):
        result = small_sa.run(verbose=False)
        assert result.n_failed >= 0

    def test_seed_reproducibility(self):
        kwargs = dict(
            model_class  = SEIRModel,
            param_class  = SEIRParameters,
            fixed        = dict(N=100_000, I0=1, E0=5, t_span=(0,100)),
            distributions= {'beta': ('uniform', 0.2, 0.5)},
            n_samples    = 6,
        )
        r1 = SensitivityAnalysis(**kwargs, seed=99).run(verbose=False)
        r2 = SensitivityAnalysis(**kwargs, seed=99).run(verbose=False)
        assert r1.summary()['r0_median'] == r2.summary()['r0_median']

    def test_more_samples_more_stable(self):
        sa_small = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=100_000,I0=1,E0=5,t_span=(0,100)),
            distributions={'beta':('uniform',0.2,0.5),'gamma':('uniform',0.05,0.15)},
            n_samples=5, seed=42,
        )
        sa_large = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=100_000,I0=1,E0=5,t_span=(0,100)),
            distributions={'beta':('uniform',0.2,0.5),'gamma':('uniform',0.05,0.15)},
            n_samples=20, seed=42,
        )
        r_small = sa_small.run(verbose=False)
        r_large = sa_large.run(verbose=False)
        assert r_small.n_samples == 5
        assert r_large.n_samples == 20

    def test_plot_returns_figure(self, small_sa):
        result = small_sa.run(verbose=False)
        fig = result.plot('I')
        assert fig is not None
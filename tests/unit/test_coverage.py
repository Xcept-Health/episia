"""
<<<<<<< HEAD
tests/unit/test_coverage_boost.py

Coverage: stats/diagnostic, stats/stratified, models/sensitivity,
          viz/plotters (mpl+plotly), viz/curves, data/types,
          data/transformers, core/utilities
=======
tests/test_final_coverage.py

Targets: viz/plotters (mpl+plotly), viz/curves, data/types,
         models/sensitivity (distributions), core/utilities
Goal: push from 69% to 80%
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
import pandas as pd
import matplotlib

<<<<<<< HEAD
from episia.stats.diagnostic import (
    diagnostic_test_2x2, roc_analysis, diagnostic_from_data,
    compare_diagnostic_tests, diagnostic_accuracy_ci,
    likelihood_ratio_ci, optimal_threshold_grid_search,
    predictive_values_from_sens_spec, fagan_nomogram,
)
from episia.stats.stratified import (
    direct_standardization, indirect_standardization,
    stratified_by_variable, mantel_haenszel_or,
)
from episia.stats.contingency import Table2x2
from episia.models import SEIRModel, SIRModel
from episia.models.parameters import SEIRParameters, SIRParameters
from episia.models.sensitivity import SensitivityAnalysis
from episia.viz.plotters import get_plotter
from episia.viz.plotters.base_plotter import PlotConfig
from episia.viz.curves import plot_epicurve, plot_trend, plot_incidence, plot_doubling
=======
from episia.viz.plotters import get_plotter
from episia.viz.curves import plot_epicurve, plot_trend, plot_incidence, plot_doubling
from episia.models import SEIRModel, SIRModel
from episia.models.parameters import SEIRParameters, SIRParameters
from episia.models.sensitivity import SensitivityAnalysis
from episia.stats.diagnostic import diagnostic_test_2x2, roc_analysis
from episia.stats.contingency import Table2x2
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb
from episia.api.results import TimeSeriesResult
from episia.data.types import (
    detect_column_types, optimize_dataframe_types,
    get_type_recommendations,
    convert_to_binary, convert_to_categorical,
    convert_to_continuous, convert_to_date,
)
<<<<<<< HEAD
from episia.data.transformers import (
    DateTransformer, CategoricalTransformer, OutlierTransformer,
    FeatureEngineer, normalize_data, create_pipeline,
)
from episia.core.utilities import EpiLoader
=======
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb


#  Fixtures 

@pytest.fixture
<<<<<<< HEAD
def binary_data():
    np.random.seed(42)
    y_true  = np.array([1]*60 + [0]*60)
    y_score = np.concatenate([np.random.beta(5,2,60), np.random.beta(2,5,60)])
    y_pred  = (y_score >= 0.5).astype(int)
    return y_true, y_score, y_pred

@pytest.fixture
def d1():  return diagnostic_test_2x2(tp=80, fp=10, fn=20, tn=90)
@pytest.fixture
def d2():  return diagnostic_test_2x2(tp=70, fp=15, fn=30, tn=85)

@pytest.fixture
def model_result():
    p = SEIRParameters(N=50_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=1/14,t_span=(0,60))
    return SEIRModel(p).run()

@pytest.fixture
def sir_result():
    p = SIRParameters(N=50_000,I0=5,beta=0.3,gamma=1/14,t_span=(0,60))
    return SIRModel(p).run()

@pytest.fixture
def roc_result(binary_data):
    y_true, y_score, _ = binary_data
    return roc_analysis(y_true, y_score)

@pytest.fixture
def diag_result():  return diagnostic_test_2x2(tp=80,fp=10,fn=20,tn=90)
=======
def model_result():
    params = SEIRParameters(N=50_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=1/14,t_span=(0,60))
    return SEIRModel(params).run()

@pytest.fixture
def sir_result():
    params = SIRParameters(N=50_000,I0=5,beta=0.3,gamma=1/14,t_span=(0,60))
    return SIRModel(params).run()

@pytest.fixture
def roc_result():
    np.random.seed(42)
    y_true  = np.array([1]*40+[0]*40)
    y_score = np.concatenate([np.random.beta(5,2,40), np.random.beta(2,5,40)])
    return roc_analysis(y_true, y_score)

@pytest.fixture
def diag_result():
    return diagnostic_test_2x2(tp=80, fp=10, fn=20, tn=90)
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb

@pytest.fixture
def ts_result():
    t = np.linspace(0, 52, 52)
    v = np.random.default_rng(0).poisson(5, 52).astype(float)
    return TimeSeriesResult(times=t, values=v)

@pytest.fixture
def sample_df():
    return pd.DataFrame({
<<<<<<< HEAD
        'date':   ['2024-01-01','2024-01-08','2024-01-15','2024-01-22'],
        'region': ['A','B','A','B'],
        'cases':  [10,20,15,5],
        'value':  [1.0,100.0,2.0,1.5],
        'flag':   [True,False,True,False],
    })

@pytest.fixture
def stratified_df():
    return pd.DataFrame({
        'exposure':  ([1,1,0,0] * 20),
        'outcome':   ([1,0,1,0] * 20),
        'age_group': (['young','old'] * 40),
    })

@pytest.fixture
def t_arr():  return np.linspace(0, 52, 52)
@pytest.fixture
def v_arr():  return np.random.default_rng(0).poisson(8, 52).astype(float)

@pytest.fixture
def sensitivity_result():
    sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
        fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
        distributions={
            'beta':  ('uniform', 0.2, 0.5),
            'gamma': ('triangular', 0.05, 0.07, 0.15),
        },
        n_samples=10, seed=42)
    return sa.run(verbose=False)


#  stats/diagnostic 

class TestDiagnosticFromData:
    def test_returns_result(self, binary_data):
        y_true,_,y_pred = binary_data
        from episia.stats.diagnostic import DiagnosticResult
        assert isinstance(diagnostic_from_data(y_true, y_pred), DiagnosticResult)

    def test_sensitivity_range(self, binary_data):
        y_true,_,y_pred = binary_data
        r = diagnostic_from_data(y_true, y_pred)
        assert 0 <= r.sensitivity <= 1

    def test_specificity_range(self, binary_data):
        y_true,_,y_pred = binary_data
        r = diagnostic_from_data(y_true, y_pred)
        assert 0 <= r.specificity <= 1

    def test_perfect_classifier(self):
        y = np.array([1,1,1,0,0,0])
        r = diagnostic_from_data(y, y)
        assert r.sensitivity == pytest.approx(1.0)
        assert r.specificity == pytest.approx(1.0)


class TestCompareDiagnosticTests:
    def test_returns_dict(self, d1, d2):
        r = compare_diagnostic_tests(d1, d2)
        assert isinstance(r, dict)

    def test_sensitivity_difference_key(self, d1, d2):
        assert 'sensitivity_difference' in compare_diagnostic_tests(d1, d2)

    def test_same_test_zero_diff(self, d1):
        r = compare_diagnostic_tests(d1, d1)
        assert abs(r['sensitivity_difference']) < 1e-10


class TestDiagnosticAccuracyCi:
    def test_returns_tuple(self):
        lo,hi = diagnostic_accuracy_ci(0.85, 200)
        assert lo < 0.85 < hi

    def test_larger_n_narrower(self):
        lo1,hi1 = diagnostic_accuracy_ci(0.8, 50)
        lo2,hi2 = diagnostic_accuracy_ci(0.8, 500)
        assert (hi1-lo1) > (hi2-lo2)


class TestLikelihoodRatioCi:
    def test_returns_tuple(self):
        lo,hi = likelihood_ratio_ci(lr=8.0, tp=80, fp=10, fn=20, tn=90)
        assert lo < 8.0 < hi


class TestPredictiveValues:
    def test_returns_tuple(self):
        ppv,npv = predictive_values_from_sens_spec(0.8, 0.9, 0.05)
        assert 0 <= ppv <= 1 and 0 <= npv <= 1

    def test_high_prevalence_higher_ppv(self):
        ppv_lo,_ = predictive_values_from_sens_spec(0.8, 0.9, 0.01)
        ppv_hi,_ = predictive_values_from_sens_spec(0.8, 0.9, 0.30)
        assert ppv_hi > ppv_lo


class TestOptimalThresholdGridSearch:
    def test_returns_dict(self, binary_data):
        y_true,y_score,_ = binary_data
        r = optimal_threshold_grid_search(y_true, y_score)
        assert isinstance(r, dict) and 'youden' in r and 'accuracy' in r


class TestFaganNomogram:
    def test_between_0_and_1(self):
        r = fagan_nomogram(pre_test_prob=0.1, lr=8.0)
        assert 0 < float(r) < 1

    def test_high_lr_higher_post_prob(self):
        lo = fagan_nomogram(pre_test_prob=0.1, lr=2.0)
        hi = fagan_nomogram(pre_test_prob=0.1, lr=20.0)
        assert float(hi) > float(lo)


#  stats/stratified 

class TestDirectStandardization:
    def test_returns_result(self):
        r = direct_standardization(
            np.array([0.02,0.05,0.10]),
            np.array([1000,500,200]),
            np.array([2000,1500,800]),
        )
        assert hasattr(r,'adjusted_rate') and r.adjusted_rate > 0

    def test_has_ci(self):
        r = direct_standardization(
            np.array([0.02,0.05,0.10]),
            np.array([1000,500,200]),
            np.array([2000,1500,800]),
        )
        assert hasattr(r, 'ci')


class TestIndirectStandardization:
    def test_returns_dict_with_smr(self):
        r = indirect_standardization(
            np.array([25,30,20]),
            np.array([1000,500,200]),
            np.array([0.02,0.05,0.08]),
        )
        assert isinstance(r, dict) and 'smr' in r and r['smr'] > 0


class TestStratifiedByVariable:
    def test_returns_stratified_table(self, stratified_df):
        from episia.stats.stratified import StratifiedTable
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        assert isinstance(st, StratifiedTable)

    def test_two_strata(self, stratified_df):
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        assert len(st.tables) == 2

    def test_strata_are_table2x2(self, stratified_df):
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        for t in st.tables:
            assert isinstance(t, Table2x2)

    def test_effect_mod_returns_dict(self, stratified_df):
        from episia.stats.stratified import test_effect_modification
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        r = test_effect_modification(st)
        assert isinstance(r, dict) and 'p_value' in r
        assert 0 <= r['p_value'] <= 1


#  models/sensitivity — all distributions + methods 

class TestSensitivityDistributions:
    def _run(self, dist, n=6):
        sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': dist}, n_samples=n, seed=0)
        return sa.run(verbose=False)

    def test_uniform(self):    assert self._run(('uniform',0.2,0.5)).n_samples == 6
    def test_normal(self):     assert self._run(('normal',0.35,0.05)).n_samples == 6
    def test_triangular(self): assert self._run(('triangular',0.2,0.35,0.5)).n_samples == 6
    def test_sir_model(self):
        sa = SensitivityAnalysis(SIRModel, SIRParameters,
            fixed=dict(N=50_000,I0=5,t_span=(0,60)),
            distributions={'beta':('uniform',0.2,0.5)}, n_samples=5, seed=0)
        assert sa.run(verbose=False).n_samples == 5


class TestSensitivityResultMethods:
    def test_to_dataframe_shape(self, sensitivity_result):
        df = sensitivity_result.to_dataframe()
        assert isinstance(df, pd.DataFrame) and len(df) == 10

    def test_to_dataframe_has_r0(self, sensitivity_result):
        assert 'r0' in sensitivity_result.to_dataframe().columns

    def test_to_dataframe_has_beta(self, sensitivity_result):
        assert 'beta' in sensitivity_result.to_dataframe().columns

    def test_plot_I_plotly(self, sensitivity_result):
        import plotly.graph_objects as go
        assert isinstance(sensitivity_result.plot('I', backend='plotly'), go.Figure)

    def test_plot_I_matplotlib(self, sensitivity_result):
        assert isinstance(sensitivity_result.plot('I', backend='matplotlib'), matplotlib.figure.Figure)

    def test_plot_S_plotly(self, sensitivity_result):
        assert sensitivity_result.plot('S') is not None

    def test_metric_dist_r0_plotly(self, sensitivity_result):
        import plotly.graph_objects as go
        assert isinstance(sensitivity_result.plot_metric_distribution('r0', backend='plotly'), go.Figure)

    def test_metric_dist_peak_plotly(self, sensitivity_result):
        assert sensitivity_result.plot_metric_distribution('peak_infected') is not None

    def test_metric_dist_matplotlib(self, sensitivity_result):
        assert isinstance(
            sensitivity_result.plot_metric_distribution('r0', backend='matplotlib'),
            matplotlib.figure.Figure
        )

    def test_summary_p5_lt_p95(self, sensitivity_result):
        s = sensitivity_result.summary()
        assert s['r0_p5'] < s['r0_p95']

    def test_envelopes_is_dict(self, sensitivity_result):
        assert isinstance(sensitivity_result.envelopes, dict) and len(sensitivity_result.envelopes) > 0


#  viz/plotters — all methods, both backends ─

class TestPlotlyPlotterMethods:
    def test_plot_model(self, model_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_model(model_result), go.Figure)

    def test_plot_sir(self, sir_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_model(sir_result), go.Figure)

    def test_plot_epicurve(self, ts_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_epicurve(ts_result), go.Figure)

    def test_plot_roc(self, roc_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_roc(roc_result), go.Figure)

    def test_plot_diagnostic(self, diag_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_diagnostic(diag_result), go.Figure)

    def test_dark_theme(self, model_result):
        fig = get_plotter('plotly').plot_model(model_result, config=PlotConfig(theme='dark'))
        assert fig is not None

    def test_minimal_theme(self, model_result):
        fig = get_plotter('plotly').plot_model(model_result, config=PlotConfig(theme='minimal'))
        assert fig is not None

    def test_colorblind_theme(self, model_result):
        fig = get_plotter('plotly').plot_model(model_result, config=PlotConfig(theme='colorblind'))
        assert fig is not None


class TestMatplotlibPlotterMethods:
    def test_plot_model(self, model_result):
        assert isinstance(get_plotter('matplotlib').plot_model(model_result), matplotlib.figure.Figure)

    def test_plot_sir(self, sir_result):
        assert isinstance(get_plotter('matplotlib').plot_model(sir_result), matplotlib.figure.Figure)

    def test_plot_epicurve(self, ts_result):
        assert isinstance(get_plotter('matplotlib').plot_epicurve(ts_result), matplotlib.figure.Figure)

    def test_plot_roc(self, roc_result):
        assert isinstance(get_plotter('matplotlib').plot_roc(roc_result), matplotlib.figure.Figure)

    def test_plot_diagnostic(self, diag_result):
        assert isinstance(get_plotter('matplotlib').plot_diagnostic(diag_result), matplotlib.figure.Figure)

    def test_dark_theme(self, model_result):
        fig = get_plotter('matplotlib').plot_model(model_result, config=PlotConfig(theme='dark'))
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_colorblind_theme(self, model_result):
        fig = get_plotter('matplotlib').plot_model(model_result, config=PlotConfig(theme='colorblind'))
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_save_figure(self, model_result, tmp_path):
        import os
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(model_result)
        path = str(tmp_path / 'fig.png')
        plotter.save(fig, path, dpi=72)
        assert os.path.exists(path) and os.path.getsize(path) > 0


#  viz/curves 

class TestPlotEpicurve:
    def test_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        assert isinstance(plot_epicurve(times=t_arr, values=v_arr, backend='plotly'), go.Figure)

    def test_matplotlib(self, t_arr, v_arr):
        assert isinstance(plot_epicurve(times=t_arr, values=v_arr, backend='matplotlib'), matplotlib.figure.Figure)

    def test_with_result_object(self, ts_result):
        assert plot_epicurve(ts_result) is not None

    def test_dark_theme(self, t_arr, v_arr):
        assert plot_epicurve(times=t_arr, values=v_arr, theme='dark') is not None

    def test_custom_labels(self, t_arr, v_arr):
        assert plot_epicurve(times=t_arr, values=v_arr, xlabel='Week', ylabel='Cases') is not None


class TestPlotTrend:
    def test_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        assert isinstance(plot_trend(times=t_arr, values=v_arr, backend='plotly'), go.Figure)

    def test_matplotlib(self, t_arr, v_arr):
        assert isinstance(plot_trend(times=t_arr, values=v_arr, backend='matplotlib'), matplotlib.figure.Figure)

    def test_no_observed(self, t_arr, v_arr):
        assert plot_trend(times=t_arr, values=v_arr, show_observed=False) is not None

    def test_minimal_theme(self, t_arr, v_arr):
        assert plot_trend(times=t_arr, values=v_arr, theme='minimal') is not None


class TestPlotIncidence:
    def test_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        rates = v_arr / 10000
        assert isinstance(plot_incidence(times=t_arr, rates=rates, backend='plotly'), go.Figure)

    def test_matplotlib(self, t_arr, v_arr):
        rates = v_arr / 10000
        assert isinstance(plot_incidence(times=t_arr, rates=rates, backend='matplotlib'), matplotlib.figure.Figure)

    def test_with_ci(self, t_arr, v_arr):
        rates = v_arr / 10000
        assert plot_incidence(times=t_arr, rates=rates, ci_lower=rates*0.8, ci_upper=rates*1.2) is not None

    def test_custom_per(self, t_arr, v_arr):
        assert plot_incidence(times=t_arr, rates=v_arr/10000, per=1000) is not None

    def test_colorblind_theme(self, t_arr, v_arr):
        assert plot_incidence(times=t_arr, rates=v_arr/10000, theme='colorblind') is not None


class TestPlotDoubling:
    def test_plotly(self):
        import plotly.graph_objects as go
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert isinstance(plot_doubling(times=t, values=v, doubling_time=1.0, backend='plotly'), go.Figure)

    def test_matplotlib(self):
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert isinstance(plot_doubling(times=t, values=v, doubling_time=1.0, backend='matplotlib'), matplotlib.figure.Figure)

    def test_without_doubling_time(self):
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert plot_doubling(times=t, values=v) is not None

    def test_custom_title(self):
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert plot_doubling(times=t, values=v, title='Growth') is not None
=======
        'date':    pd.date_range('2024-01-01', periods=20, freq='W'),
        'cases':   np.random.default_rng(0).poisson(5, 20),
        'region':  ['A','B','C','D'] * 5,
        'rate':    np.random.default_rng(0).random(20),
        'flag':    [True, False] * 10,
    })

@pytest.fixture
def t_arr():
    return np.linspace(0, 52, 52)

@pytest.fixture
def v_arr():
    return np.random.default_rng(0).poisson(8, 52).astype(float)


#  Plotly plotter — all methods 

class TestPlotlyPlotterModel:

    def test_plot_model_returns_figure(self, model_result):
        import plotly.graph_objects as go
        plotter = get_plotter('plotly')
        fig = plotter.plot_model(model_result)
        assert isinstance(fig, go.Figure)

    def test_plot_model_sir(self, sir_result):
        import plotly.graph_objects as go
        fig = get_plotter('plotly').plot_model(sir_result)
        assert isinstance(fig, go.Figure)

    def test_plot_epicurve_returns_figure(self, ts_result):
        import plotly.graph_objects as go
        fig = get_plotter('plotly').plot_epicurve(ts_result)
        assert isinstance(fig, go.Figure)

    def test_plot_roc_returns_figure(self, roc_result):
        import plotly.graph_objects as go
        fig = get_plotter('plotly').plot_roc(roc_result)
        assert isinstance(fig, go.Figure)

    def test_plot_diagnostic_returns_figure(self, diag_result):
        import plotly.graph_objects as go
        fig = get_plotter('plotly').plot_diagnostic(diag_result)
        assert isinstance(fig, go.Figure)

    def test_plot_model_dark_theme(self, model_result):
        from episia.viz.plotters.base_plotter import PlotConfig
        plotter = get_plotter('plotly')
        fig = plotter.plot_model(model_result, config=PlotConfig(theme='dark'))
        assert fig is not None

    def test_plot_model_minimal_theme(self, model_result):
        from episia.viz.plotters.base_plotter import PlotConfig
        plotter = get_plotter('plotly')
        fig = plotter.plot_model(model_result, config=PlotConfig(theme='minimal'))
        assert fig is not None


#  Matplotlib plotter — all methods 

class TestMatplotlibPlotterModel:

    def test_plot_model_returns_figure(self, model_result):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(model_result)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_sir_returns_figure(self, sir_result):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(sir_result)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_epicurve_returns_figure(self, ts_result):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_epicurve(ts_result)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_roc_returns_figure(self, roc_result):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_roc(roc_result)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_diagnostic_returns_figure(self, diag_result):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_diagnostic(diag_result)
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_model_dark_theme(self, model_result):
        from episia.viz.plotters.base_plotter import PlotConfig
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(model_result, config=PlotConfig(theme='dark'))
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_plot_model_colorblind_theme(self, model_result):
        from episia.viz.plotters.base_plotter import PlotConfig
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(model_result, config=PlotConfig(theme='colorblind'))
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_save_figure(self, model_result, tmp_path):
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(model_result)
        path = str(tmp_path / 'test.png')
        plotter.save(fig, path, dpi=72)
        import os
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0


#  viz/curves — all functions, both backends 

class TestPlotEpicurve:

    def test_plotly_returns_figure(self, t_arr, v_arr):
        import plotly.graph_objects as go
        fig = plot_epicurve(times=t_arr, values=v_arr, backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_matplotlib_returns_figure(self, t_arr, v_arr):
        fig = plot_epicurve(times=t_arr, values=v_arr, backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_custom_title(self, t_arr, v_arr):
        fig = plot_epicurve(times=t_arr, values=v_arr, title='Weekly cases')
        assert fig is not None

    def test_dark_theme(self, t_arr, v_arr):
        fig = plot_epicurve(times=t_arr, values=v_arr, theme='dark')
        assert fig is not None

    def test_with_timeseries_result(self, ts_result):
        fig = plot_epicurve(ts_result)
        assert fig is not None

    def test_custom_labels(self, t_arr, v_arr):
        fig = plot_epicurve(times=t_arr, values=v_arr,
                            xlabel='Week', ylabel='Cases')
        assert fig is not None


class TestPlotTrend:

    def test_plotly_returns_figure(self, t_arr, v_arr):
        import plotly.graph_objects as go
        fig = plot_trend(times=t_arr, values=v_arr, backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_matplotlib_returns_figure(self, t_arr, v_arr):
        fig = plot_trend(times=t_arr, values=v_arr, backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_without_observed(self, t_arr, v_arr):
        fig = plot_trend(times=t_arr, values=v_arr, show_observed=False)
        assert fig is not None

    def test_custom_title(self, t_arr, v_arr):
        fig = plot_trend(times=t_arr, values=v_arr, title='Trend Analysis')
        assert fig is not None

    def test_minimal_theme(self, t_arr, v_arr):
        fig = plot_trend(times=t_arr, values=v_arr, theme='minimal')
        assert fig is not None


class TestPlotIncidence:

    def test_plotly_returns_figure(self, t_arr, v_arr):
        import plotly.graph_objects as go
        rates = v_arr / 10000
        fig = plot_incidence(times=t_arr, rates=rates, backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_matplotlib_returns_figure(self, t_arr, v_arr):
        rates = v_arr / 10000
        fig = plot_incidence(times=t_arr, rates=rates, backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_with_ci(self, t_arr, v_arr):
        rates = v_arr / 10000
        ci_lo = rates * 0.8
        ci_hi = rates * 1.2
        fig = plot_incidence(times=t_arr, rates=rates, ci_lower=ci_lo, ci_upper=ci_hi)
        assert fig is not None

    def test_custom_per(self, t_arr, v_arr):
        rates = v_arr / 10000
        fig = plot_incidence(times=t_arr, rates=rates, per=1000)
        assert fig is not None

    def test_colorblind_theme(self, t_arr, v_arr):
        rates = v_arr / 10000
        fig = plot_incidence(times=t_arr, rates=rates, theme='colorblind')
        assert fig is not None
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb


#  data/types 

class TestDetectColumnTypes:
<<<<<<< HEAD
    def test_returns_dict(self, sample_df):
        r = detect_column_types(sample_df)
        assert isinstance(r, dict) and len(r) == len(sample_df.columns)

    def test_continuous_detected(self):
        df = pd.DataFrame({'rate':[0.1,0.5,0.8,0.3,0.2,0.7]})
        assert detect_column_types(df)['rate'] == 'continuous'


class TestOptimizeDataframeTypes:
    def test_returns_df(self, sample_df):
        r = optimize_dataframe_types(sample_df)
        assert isinstance(r, pd.DataFrame) and len(r) == len(sample_df)

    def test_same_columns(self, sample_df):
        r = optimize_dataframe_types(sample_df)
        assert set(r.columns) == set(sample_df.columns)

    def test_downcast_integers(self):
        df = pd.DataFrame({'n': np.array([1,2,3,4], dtype=np.int64)})
        r = optimize_dataframe_types(df, downcast_integers=True)
        assert isinstance(r, pd.DataFrame)

    def test_no_downcast_floats(self):
        df = pd.DataFrame({'x': [1.0,2.0,3.0]})
        assert isinstance(optimize_dataframe_types(df, downcast_floats=False), pd.DataFrame)


class TestGetTypeRecommendations:
    def test_returns_dataframe(self, sample_df):
        assert isinstance(get_type_recommendations(sample_df), pd.DataFrame)


class TestConvertFunctions:
    def test_binary(self):
        r = convert_to_binary(pd.Series([True,False,True,False]))
        assert set(r.unique()).issubset({0,1})

    def test_categorical(self):
        r = convert_to_categorical(pd.Series(['A','B','A','C']))
        assert r.dtype.name == 'category'

    def test_continuous(self):
        r = convert_to_continuous(pd.Series([1,2,3,4]))
        assert np.issubdtype(r.dtype, np.number)

    def test_continuous_from_strings(self):
        r = convert_to_continuous(pd.Series(['1.5','2.3','3.1']))
        assert np.issubdtype(r.dtype, np.number)

    def test_date_from_strings(self):
        r = convert_to_date(pd.Series(['2024-01-01','2024-01-08']))
        assert np.issubdtype(r.dtype, np.datetime64)

    def test_date_already_datetime(self):
        r = convert_to_date(pd.Series(pd.date_range('2024-01-01', periods=4)))
        assert np.issubdtype(r.dtype, np.datetime64)


#  data/transformers ─

class TestNormalizeData:
    def test_standard_mean_zero(self):
        df = pd.DataFrame({'a':[1.,2.,3.,4.,5.],'b':[10.,20.,30.,40.,50.]})
        r = normalize_data(df, columns=['a','b'], method='standard')
        assert abs(r['a'].mean()) < 1e-10

    def test_minmax_range(self):
        df = pd.DataFrame({'a':[1.,2.,3.,4.,5.]})
        r = normalize_data(df, columns=['a'], method='minmax')
        assert r['a'].min() == pytest.approx(0.0) and r['a'].max() == pytest.approx(1.0)


class TestOutlierTransformerActions:
    def test_clip_action(self):
        df = pd.DataFrame({'v':[1.,2.,100.,1.5]})
        r = OutlierTransformer(numeric_columns=['v'], action='clip').fit_transform(df.copy())
        assert r['v'].max() < 100.

    def test_remove_action(self):
        df = pd.DataFrame({'v':[1.,2.,100.,1.5,1.8]})
        r = OutlierTransformer(numeric_columns=['v'], action='remove').fit_transform(df.copy())
        assert len(r) < len(df)

    def test_zscore_method(self):
        df = pd.DataFrame({'v':[1.,2.,3.,50.,2.,1.,3.]})
        r = OutlierTransformer(numeric_columns=['v'], method='zscore', threshold=2.0).fit_transform(df.copy())
        assert isinstance(r, pd.DataFrame)


class TestFeatureEngineer:
    def test_returns_dataframe(self):
        df = pd.DataFrame({
            'date':   pd.date_range('2024-01-01', periods=5, freq='W'),
            'cases':  [10,20,15,5,8],
            'region': ['A','B','A','B','A'],
        })
        r = FeatureEngineer().transform(df.copy())
        assert isinstance(r, pd.DataFrame) and len(r) == len(df)


class TestCreatePipeline:
    def test_pipeline_callable(self):
        pipe = create_pipeline([DateTransformer(date_columns='date')])
        assert callable(pipe)

    def test_pipeline_applies(self):
        df = pd.DataFrame({
            'date':   ['2024-01-01','2024-01-08','2024-01-15'],
            'cases':  [10,20,15],
            'region': ['A','B','A'],
        })
        pipe = create_pipeline([DateTransformer(date_columns='date')])
        r = pipe(df.copy())
        assert 'date_year' in r.columns


#  core/utilities — EpiLoader 

class TestEpiLoader:
    def test_instantiates(self):
        loader = EpiLoader("test")
        assert loader is not None

    def test_custom_width(self):
        loader = EpiLoader("test", width=60)
        assert loader is not None

    def test_is_tty_returns_bool(self):
        loader = EpiLoader("test")
        assert isinstance(loader._is_tty(), bool)

    def test_context_manager_silent_in_ci(self):
        # Non-TTY (CI/test env): should run silently without raising
        with EpiLoader("Silent test"):
            x = 1 + 1
        assert x == 2

    def test_context_manager_with_exception(self):
        try:
            with EpiLoader("Error test"):
                raise ValueError("test error")
        except ValueError:
            pass  # exception propagates correctly

    def test_spinner_alias(self):
        from episia.core.utilities import Spinner
        with Spinner("Spinner alias test"):
            pass

    def test_multiple_contexts(self):
        for msg in ["Step 1","Step 2","Step 3"]:
            with EpiLoader(msg):
                pass

    def test_check_unicode_returns_bool(self):
        loader = EpiLoader("test")
        assert isinstance(loader._check_unicode(), bool)

    def test_check_color_returns_bool(self):
        loader = EpiLoader("test")
        assert isinstance(loader._check_color(), bool)
=======

    def test_returns_dict(self, sample_df):
        result = detect_column_types(sample_df)
        assert isinstance(result, dict)

    def test_all_columns_present(self, sample_df):
        result = detect_column_types(sample_df)
        for col in sample_df.columns:
            assert col in result

    def test_binary_detected(self):
        df = pd.DataFrame({'flag': [True, False, True, False]})
        result = detect_column_types(df)
        assert result['flag'] in ('binary', 'categorical', 'continuous')

    def test_continuous_detected(self):
        df = pd.DataFrame({'rate': [0.1, 0.5, 0.8, 0.3]})
        result = detect_column_types(df)
        assert result['rate'] == 'continuous'

    def test_returns_strings(self, sample_df):
        result = detect_column_types(sample_df)
        for v in result.values():
            assert isinstance(v, str)


class TestOptimizeDataframeTypes:

    def test_returns_dataframe(self, sample_df):
        result = optimize_dataframe_types(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_same_row_count(self, sample_df):
        result = optimize_dataframe_types(sample_df)
        assert len(result) == len(sample_df)

    def test_same_columns(self, sample_df):
        result = optimize_dataframe_types(sample_df)
        assert set(result.columns) == set(sample_df.columns)

    def test_integer_downcasting(self):
        df = pd.DataFrame({'count': np.array([1, 2, 3, 4], dtype=np.int64)})
        result = optimize_dataframe_types(df, downcast_integers=True)
        assert result['count'].dtype.itemsize <= 8

    def test_no_downcast(self):
        df = pd.DataFrame({'x': np.array([1.0, 2.0, 3.0])})
        result = optimize_dataframe_types(df, downcast_floats=False)
        assert isinstance(result, pd.DataFrame)


class TestGetTypeRecommendations:

    def test_returns_dataframe(self, sample_df):
        result = get_type_recommendations(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_columns(self, sample_df):
        result = get_type_recommendations(sample_df)
        assert len(result.columns) > 0


class TestConvertFunctions:

    def test_convert_to_binary(self):
        s = pd.Series([True, False, True, False])
        result = convert_to_binary(s)
        assert isinstance(result, pd.Series)
        assert set(result.unique()).issubset({0, 1})

    def test_convert_to_binary_integers(self):
        s = pd.Series([1, 0, 1, 0])
        result = convert_to_binary(s)
        assert isinstance(result, pd.Series)

    def test_convert_to_categorical(self):
        s = pd.Series(['A', 'B', 'A', 'C'])
        result = convert_to_categorical(s)
        assert result.dtype.name == 'category'

    def test_convert_to_categorical_max_categories(self):
        s = pd.Series(['A', 'B', 'C', 'D', 'E'] * 4)
        result = convert_to_categorical(s, max_categories=3)
        assert isinstance(result, pd.Series)

    def test_convert_to_continuous(self):
        s = pd.Series([1, 2, 3, 4])
        result = convert_to_continuous(s)
        assert np.issubdtype(result.dtype, np.number)

    def test_convert_to_continuous_strings(self):
        s = pd.Series(['1.5', '2.3', '3.1'])
        result = convert_to_continuous(s)
        assert np.issubdtype(result.dtype, np.number)

    def test_convert_to_date(self):
        s = pd.Series(['2024-01-01', '2024-01-08', '2024-01-15'])
        result = convert_to_date(s)
        assert np.issubdtype(result.dtype, np.datetime64)

    def test_convert_to_date_already_datetime(self):
        s = pd.Series(pd.date_range('2024-01-01', periods=5))
        result = convert_to_date(s)
        assert np.issubdtype(result.dtype, np.datetime64)


#  models/sensitivity — all distributions 

class TestSensitivityDistributions:

    def test_uniform_distribution(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': ('uniform', 0.2, 0.5)},
            n_samples=6, seed=0,
        )
        r = sa.run(verbose=False)
        assert r.n_samples == 6

    def test_normal_distribution(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': ('normal', 0.35, 0.05)},
            n_samples=6, seed=1,
        )
        r = sa.run(verbose=False)
        assert r.n_samples == 6

    def test_triangular_distribution(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'gamma': ('triangular', 0.05, 0.07, 0.15)},
            n_samples=6, seed=2,
        )
        r = sa.run(verbose=False)
        assert r.n_samples == 6

    def test_multiple_distributions(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={
                'beta':  ('uniform', 0.2, 0.5),
                'gamma': ('normal',  0.07, 0.02),
            },
            n_samples=8, seed=42,
        )
        r = sa.run(verbose=False)
        assert r.n_samples == 8
        assert 'r0_median' in r.summary()

    def test_sir_model_sensitivity(self):
        sa = SensitivityAnalysis(
            SIRModel, SIRParameters,
            fixed=dict(N=50_000,I0=5,t_span=(0,60)),
            distributions={'beta': ('uniform', 0.2, 0.5)},
            n_samples=5, seed=0,
        )
        r = sa.run(verbose=False)
        assert r.n_samples == 5

    def test_large_n_samples(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': ('uniform', 0.2, 0.5)},
            n_samples=20, seed=0,
        )
        r = sa.run(verbose=False)
        df = r.to_dataframe()
        assert len(df) == 20

    def test_envelopes_have_compartments(self):
        sa = SensitivityAnalysis(
            SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': ('uniform', 0.2, 0.5)},
            n_samples=5, seed=0,
        )
        r = sa.run(verbose=False)
        assert isinstance(r.envelopes, dict)
        assert len(r.envelopes) > 0
>>>>>>> 0ed51c3c2a6f7ae1f8a69df6f7ac4ed9472767eb

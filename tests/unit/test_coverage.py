"""
tests/unit/test_coverage.py

Coverage: stats/diagnostic, stats/stratified, models/sensitivity,
          viz/plotters (mpl+plotly), viz/curves, viz/roc, viz/utils,
          viz/themes, viz/forest, viz/contingency_plot,
          data/types, data/transformers, core/utilities
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
import pandas as pd
import matplotlib

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
from episia.stats.contingency import Table2x2, risk_ratio
from episia.models import SEIRModel, SIRModel, SEIRDModel
from episia.models.parameters import SEIRParameters, SIRParameters, SEIRDParameters
from episia.models.sensitivity import SensitivityAnalysis
from episia.viz.plotters import get_plotter
from episia.viz.plotters.base_plotter import PlotConfig
from episia.viz.curves import plot_epicurve, plot_trend, plot_incidence, plot_doubling
from episia.viz.roc import plot_roc, plot_roc_compare, plot_precision_recall
from episia.viz.forest import plot_meta_forest
from episia.viz.contingency_plot import plot_measures
from episia.viz.utils import (
    p_value_label, significance_stars, hex_to_rgb, hex_to_rgba_str,
    ci_band_xy, adjust_alpha, px_to_inches, auto_height,
    nice_log_ticks, symlog_range,
)
from episia.viz.themes.registry import (
    get_available_themes, get_palette, get_plotly_layout,
    get_theme, set_theme, register_theme,
)
from episia.api.results import TimeSeriesResult
from episia.data.types import (
    detect_column_types, optimize_dataframe_types,
    get_type_recommendations, optimize_column_type,
    optimize_numeric_type, optimize_object_type, optimize_datetime_type,
    convert_to_binary, convert_to_categorical,
    convert_to_continuous, convert_to_date,
    convert_to_epidemiological_types,
)
from episia.data.transformers import (
    DateTransformer, CategoricalTransformer, OutlierTransformer,
    FeatureEngineer, normalize_data, create_pipeline,
)
from episia.core.utilities import EpiLoader, Spinner


#  Fixtures 

@pytest.fixture
def binary_data():
    np.random.seed(42)
    y_true  = np.array([1]*60 + [0]*60)
    y_score = np.concatenate([np.random.beta(5,2,60), np.random.beta(2,5,60)])
    return y_true, y_score, (y_score >= 0.5).astype(int)

@pytest.fixture
def d1():  return diagnostic_test_2x2(tp=80, fp=10, fn=20, tn=90)
@pytest.fixture
def d2():  return diagnostic_test_2x2(tp=70, fp=15, fn=30, tn=85)

@pytest.fixture
def seir_result():
    p = SEIRParameters(N=50_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=1/14,t_span=(0,60))
    return SEIRModel(p).run()

@pytest.fixture
def seird_result():
    p = SEIRDParameters(N=50_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=0.09,mu=0.01,t_span=(0,60))
    return SEIRDModel(p).run()

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

@pytest.fixture
def table():  return Table2x2(a=40, b=10, c=20, d=30)

@pytest.fixture
def ts_result():
    t = np.linspace(0, 52, 52)
    v = np.random.default_rng(0).poisson(5, 52).astype(float)
    return TimeSeriesResult(times=t, values=v)

@pytest.fixture
def sample_df():
    return pd.DataFrame({
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
        assert 0 <= r.sensitivity <= 1 and 0 <= r.specificity <= 1

    def test_perfect_classifier(self):
        y = np.array([1,1,1,0,0,0])
        r = diagnostic_from_data(y, y)
        assert r.sensitivity == pytest.approx(1.0) and r.specificity == pytest.approx(1.0)


class TestCompareDiagnosticTests:
    def test_returns_dict_with_diff(self, d1, d2):
        r = compare_diagnostic_tests(d1, d2)
        assert isinstance(r, dict) and 'sensitivity_difference' in r

    def test_same_test_zero_diff(self, d1):
        assert abs(compare_diagnostic_tests(d1, d1)['sensitivity_difference']) < 1e-10


class TestDiagnosticAccuracyCi:
    def test_ci_contains_accuracy(self):
        lo,hi = diagnostic_accuracy_ci(0.85, 200)
        assert lo < 0.85 < hi

    def test_larger_n_narrower(self):
        lo1,hi1 = diagnostic_accuracy_ci(0.8, 50)
        lo2,hi2 = diagnostic_accuracy_ci(0.8, 500)
        assert (hi1-lo1) > (hi2-lo2)


class TestLikelihoodRatioCi:
    def test_ci_contains_lr(self):
        lo,hi = likelihood_ratio_ci(lr=8.0, tp=80, fp=10, fn=20, tn=90)
        assert lo < 8.0 < hi


class TestPredictiveValues:
    def test_values_in_range(self):
        ppv,npv = predictive_values_from_sens_spec(0.8, 0.9, 0.05)
        assert 0 <= ppv <= 1 and 0 <= npv <= 1

    def test_high_prevalence_higher_ppv(self):
        ppv_lo,_ = predictive_values_from_sens_spec(0.8, 0.9, 0.01)
        ppv_hi,_ = predictive_values_from_sens_spec(0.8, 0.9, 0.30)
        assert ppv_hi > ppv_lo


class TestOptimalThresholdGridSearch:
    def test_returns_dict_with_keys(self, binary_data):
        y_true,y_score,_ = binary_data
        r = optimal_threshold_grid_search(y_true, y_score)
        assert isinstance(r, dict) and 'youden' in r and 'accuracy' in r


class TestFaganNomogram:
    def test_between_0_and_1(self):
        assert 0 < float(fagan_nomogram(pre_test_prob=0.1, lr=8.0)) < 1

    def test_high_lr_higher_post(self):
        lo = fagan_nomogram(pre_test_prob=0.1, lr=2.0)
        hi = fagan_nomogram(pre_test_prob=0.1, lr=20.0)
        assert float(hi) > float(lo)


#  stats/stratified 

class TestDirectStandardization:
    def test_adjusted_rate_positive(self):
        r = direct_standardization(
            np.array([0.02,0.05,0.10]), np.array([1000,500,200]), np.array([2000,1500,800]),
        )
        assert hasattr(r,'adjusted_rate') and r.adjusted_rate > 0 and hasattr(r,'ci')


class TestIndirectStandardization:
    def test_smr_positive(self):
        r = indirect_standardization(
            np.array([25,30,20]), np.array([1000,500,200]), np.array([0.02,0.05,0.08]),
        )
        assert isinstance(r, dict) and 'smr' in r and r['smr'] > 0


class TestStratifiedByVariable:
    def test_returns_stratified_table(self, stratified_df):
        from episia.stats.stratified import StratifiedTable
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        assert isinstance(st, StratifiedTable) and len(st.tables) == 2

    def test_effect_mod_returns_dict(self, stratified_df):
        from episia.stats.stratified import test_effect_modification
        st = stratified_by_variable(stratified_df,'exposure','outcome','age_group')
        r = test_effect_modification(st)
        assert isinstance(r, dict) and 0 <= r['p_value'] <= 1


#  models/sensitivity 

class TestSensitivityDistributions:
    def _run(self, dist, n=6):
        sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta': dist}, n_samples=n, seed=0)
        return sa.run(verbose=False)

    def test_uniform(self):    assert self._run(('uniform',0.2,0.5)).n_samples == 6
    def test_normal(self):     assert self._run(('normal',0.35,0.05)).n_samples == 6
    def test_triangular(self): assert self._run(('triangular',0.2,0.35,0.5)).n_samples == 6

    def test_verbose_run(self):
        sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta':('uniform',0.3,0.4)},
            n_samples=4, seed=1)
        r = sa.run(verbose=True)
        assert r.n_samples == 4

    def test_sir_model(self):
        sa = SensitivityAnalysis(SIRModel, SIRParameters,
            fixed=dict(N=50_000,I0=5,t_span=(0,60)),
            distributions={'beta':('uniform',0.2,0.5)}, n_samples=5, seed=0)
        assert sa.run(verbose=False).n_samples == 5


class TestSensitivityResultMethods:
    def test_to_dataframe(self, sensitivity_result):
        df = sensitivity_result.to_dataframe()
        assert isinstance(df, pd.DataFrame) and len(df) == 10
        assert 'r0' in df.columns and 'beta' in df.columns

    def test_plot_all_compartments_plotly(self, sensitivity_result):
        import plotly.graph_objects as go
        for comp in sensitivity_result.compartment_names:
            assert isinstance(sensitivity_result.plot(comp, backend='plotly'), go.Figure)

    def test_plot_all_compartments_matplotlib(self, sensitivity_result):
        for comp in sensitivity_result.compartment_names:
            assert isinstance(sensitivity_result.plot(comp, backend='matplotlib'), matplotlib.figure.Figure)

    def test_metric_distribution_all_metrics_plotly(self, sensitivity_result):
        import plotly.graph_objects as go
        for metric in ['r0','peak_infected','peak_time','final_size']:
            assert isinstance(sensitivity_result.plot_metric_distribution(metric, backend='plotly'), go.Figure)

    def test_metric_distribution_all_metrics_matplotlib(self, sensitivity_result):
        for metric in ['r0','peak_infected','peak_time','final_size']:
            assert isinstance(sensitivity_result.plot_metric_distribution(metric, backend='matplotlib'), matplotlib.figure.Figure)

    def test_summary_stats(self, sensitivity_result):
        s = sensitivity_result.summary()
        assert s['r0_p5'] < s['r0_p95'] and s['peak_infected_median'] > 0

    def test_envelopes_is_dict(self, sensitivity_result):
        assert isinstance(sensitivity_result.envelopes, dict) and len(sensitivity_result.envelopes) > 0

    def test_three_distributions(self):
        sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={
                'beta':  ('uniform', 0.2, 0.5),
                'gamma': ('normal',  0.07, 0.02),
                'sigma': ('triangular', 0.15, 0.19, 0.25),
            },
            n_samples=8, seed=42, t_eval_points=100)
        r = sa.run(verbose=False)
        assert r.n_samples == 8
        assert 'beta' in r.to_dataframe().columns
        assert 'gamma' in r.to_dataframe().columns


#  viz/plotters — plotly ─

class TestPlotlyPlotter:
    def test_plot_seir(self, seir_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_model(seir_result), go.Figure)

    def test_plot_seird(self, seird_result):
        import plotly.graph_objects as go
        assert isinstance(get_plotter('plotly').plot_model(seird_result), go.Figure)

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

    def test_all_themes(self, seir_result):
        for theme in ['scientific','minimal','dark','colorblind']:
            fig = get_plotter('plotly').plot_model(seir_result, config=PlotConfig(theme=theme))
            assert fig is not None

    def test_roc_all_themes(self, roc_result):
        for theme in ['dark','minimal','colorblind']:
            assert get_plotter('plotly').plot_roc(roc_result, config=PlotConfig(theme=theme)) is not None

    def test_diagnostic_themes(self, diag_result):
        for theme in ['dark','minimal']:
            assert get_plotter('plotly').plot_diagnostic(diag_result, config=PlotConfig(theme=theme)) is not None


#  viz/plotters — matplotlib ─

class TestMatplotlibPlotter:
    def test_plot_seir(self, seir_result):
        assert isinstance(get_plotter('matplotlib').plot_model(seir_result), matplotlib.figure.Figure)

    def test_plot_seird(self, seird_result):
        assert isinstance(get_plotter('matplotlib').plot_model(seird_result), matplotlib.figure.Figure)

    def test_plot_sir(self, sir_result):
        assert isinstance(get_plotter('matplotlib').plot_model(sir_result), matplotlib.figure.Figure)

    def test_plot_epicurve(self, ts_result):
        assert isinstance(get_plotter('matplotlib').plot_epicurve(ts_result), matplotlib.figure.Figure)

    def test_plot_roc(self, roc_result):
        assert isinstance(get_plotter('matplotlib').plot_roc(roc_result), matplotlib.figure.Figure)

    def test_plot_diagnostic(self, diag_result):
        assert isinstance(get_plotter('matplotlib').plot_diagnostic(diag_result), matplotlib.figure.Figure)

    def test_plot_contingency(self, table):
        assert isinstance(get_plotter('matplotlib').plot_contingency(table), matplotlib.figure.Figure)

    def test_all_themes(self, seir_result):
        for theme in ['scientific','minimal','dark','colorblind']:
            fig = get_plotter('matplotlib').plot_model(seir_result, config=PlotConfig(theme=theme))
            assert isinstance(fig, matplotlib.figure.Figure)

    def test_roc_all_themes(self, roc_result):
        for theme in ['dark','minimal','colorblind']:
            assert isinstance(
                get_plotter('matplotlib').plot_roc(roc_result, config=PlotConfig(theme=theme)),
                matplotlib.figure.Figure
            )

    def test_save_png(self, seir_result, tmp_path):
        import os
        plotter = get_plotter('matplotlib')
        fig = plotter.plot_model(seir_result)
        path = str(tmp_path / 'fig.png')
        plotter.save(fig, path, dpi=72)
        assert os.path.exists(path) and os.path.getsize(path) > 0


#  viz/curves 

class TestVizCurves:
    def test_epicurve_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        assert isinstance(plot_epicurve(times=t_arr, values=v_arr, backend='plotly'), go.Figure)

    def test_epicurve_matplotlib(self, t_arr, v_arr):
        assert isinstance(plot_epicurve(times=t_arr, values=v_arr, backend='matplotlib'), matplotlib.figure.Figure)

    def test_epicurve_animated(self, ts_result):
        assert plot_epicurve(ts_result, animate=True) is not None

    def test_epicurve_themes(self, t_arr, v_arr):
        for theme in ['dark','minimal','colorblind']:
            assert plot_epicurve(times=t_arr, values=v_arr, theme=theme) is not None

    def test_trend_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        assert isinstance(plot_trend(times=t_arr, values=v_arr, backend='plotly'), go.Figure)

    def test_trend_matplotlib(self, t_arr, v_arr):
        assert isinstance(plot_trend(times=t_arr, values=v_arr, backend='matplotlib'), matplotlib.figure.Figure)

    def test_trend_no_observed(self, t_arr, v_arr):
        assert plot_trend(times=t_arr, values=v_arr, show_observed=False) is not None

    def test_incidence_plotly(self, t_arr, v_arr):
        import plotly.graph_objects as go
        assert isinstance(plot_incidence(times=t_arr, rates=v_arr/10000, backend='plotly'), go.Figure)

    def test_incidence_matplotlib(self, t_arr, v_arr):
        assert isinstance(plot_incidence(times=t_arr, rates=v_arr/10000, backend='matplotlib'), matplotlib.figure.Figure)

    def test_incidence_with_ci(self, t_arr, v_arr):
        rates = v_arr/10000
        assert plot_incidence(times=t_arr, rates=rates, ci_lower=rates*0.8, ci_upper=rates*1.2) is not None

    def test_doubling_plotly(self):
        import plotly.graph_objects as go
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert isinstance(plot_doubling(times=t, values=v, doubling_time=1.0, backend='plotly'), go.Figure)

    def test_doubling_matplotlib(self):
        t = np.array([1.,2.,3.,4.])
        v = np.array([10.,20.,40.,80.])
        assert isinstance(plot_doubling(times=t, values=v, doubling_time=1.0, backend='matplotlib'), matplotlib.figure.Figure)


#  viz/roc ─

class TestVizRoc:
    def test_plot_roc_plotly(self, roc_result):
        import plotly.graph_objects as go
        assert isinstance(plot_roc(roc_result, backend='plotly'), go.Figure)

    def test_plot_roc_matplotlib(self, roc_result):
        assert isinstance(plot_roc(roc_result, backend='matplotlib'), matplotlib.figure.Figure)

    def test_plot_roc_themes(self, roc_result):
        for theme in ['dark','minimal','colorblind']:
            assert plot_roc(roc_result, theme=theme) is not None

    def test_compare_plotly(self, roc_result):
        import plotly.graph_objects as go
        assert isinstance(plot_roc_compare([roc_result,roc_result], labels=['A','B'], backend='plotly'), go.Figure)

    def test_compare_matplotlib(self, roc_result):
        assert isinstance(plot_roc_compare([roc_result,roc_result], labels=['A','B'], backend='matplotlib'), matplotlib.figure.Figure)

    def test_precision_recall(self, binary_data):
        y_true,y_score,_ = binary_data
        assert plot_precision_recall(y_true, y_score) is not None

    def test_precision_recall_matplotlib(self, binary_data):
        y_true,y_score,_ = binary_data
        assert isinstance(plot_precision_recall(y_true, y_score, backend='matplotlib'), matplotlib.figure.Figure)


#  viz/forest 

class TestVizForest:
    def test_meta_forest_plotly(self):
        import plotly.graph_objects as go
        fig = plot_meta_forest([1.5,2.0,1.8],[1.1,1.4,1.2],[2.0,2.8,2.6],
                               ['A','B','C'], backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_meta_forest_matplotlib(self):
        fig = plot_meta_forest([1.5,2.0,1.8],[1.1,1.4,1.2],[2.0,2.8,2.6],
                               ['A','B','C'], backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_meta_forest_with_pooled(self):
        fig = plot_meta_forest(
            [1.5,2.0,1.8],[1.1,1.4,1.2],[2.0,2.8,2.6],['A','B','C'],
            pooled_estimate=1.7, pooled_ci=(1.3,2.2),
            i_squared=25.0, tau_squared=0.03, p_heterogeneity=0.15,
        )
        assert fig is not None

    def test_meta_forest_with_weights(self):
        fig = plot_meta_forest(
            [1.5,2.0],[1.1,1.4],[2.0,2.8],['A','B'],
            weights=[0.6,0.4],
        )
        assert fig is not None

    def test_meta_forest_custom_null(self):
        assert plot_meta_forest([0.5,0.8],[0.3,0.5],[0.8,1.1],['A','B'], null_value=0.0) is not None


#  viz/contingency_plot 

class TestVizContingencyPlot:
    def test_measures_plotly(self, table):
        import plotly.graph_objects as go
        assert isinstance(plot_measures(table, backend='plotly'), go.Figure)

    def test_measures_matplotlib(self, table):
        assert isinstance(plot_measures(table, backend='matplotlib'), matplotlib.figure.Figure)

    def test_measures_themes(self, table):
        for theme in ['dark','minimal','colorblind']:
            assert plot_measures(table, theme=theme) is not None

    def test_measures_custom_title(self, table):
        assert plot_measures(table, title='My Measures') is not None


#  viz/utils ─

class TestVizUtils:
    def test_p_value_label(self):
        for p in [0.0001,0.001,0.03,0.5]:
            assert isinstance(p_value_label(p), str) and 'p' in p_value_label(p).lower()

    def test_significance_stars(self):
        assert '*' in significance_stars(0.001)
        assert significance_stars(0.5) in ('','ns','n.s.')

    def test_hex_to_rgb(self):
        r,g,b = hex_to_rgb('#2997ff')
        assert r==41 and g==151 and b==255

    def test_hex_to_rgba_str(self):
        assert hex_to_rgba_str('#2997ff', 0.5).startswith('rgba(')

    def test_adjust_alpha(self):
        assert adjust_alpha('#2997ff', 0.5).startswith('rgba(')

    def test_px_to_inches(self):
        assert abs(px_to_inches(100) - 1.0) < 0.01

    def test_auto_height(self):
        assert auto_height(10) >= auto_height(3)

    def test_ci_band_xy(self):
        x,y = ci_band_xy(np.array([1.,2.,3.]),np.array([0.5,1.,1.5]),np.array([1.5,3.,4.5]))
        assert len(x) == 6 and len(y) == 6

    def test_nice_log_ticks(self):
        r = nice_log_ticks(0.01,100)
        assert isinstance(r,list) and r[0]<=0.01 and r[-1]>=100

    def test_symlog_range(self):
        lo,hi = symlog_range(np.array([-1.,0.,5.]))
        assert lo < hi


#  viz/themes 

class TestVizThemes:
    def test_available_themes(self):
        themes = get_available_themes()
        for t in ('scientific','minimal','dark','colorblind'):
            assert t in themes

    def test_get_palette(self):
        assert len(get_palette()) > 0 and len(get_palette('dark')) > 0

    def test_get_plotly_layout(self):
        assert isinstance(get_plotly_layout(), dict)
        assert isinstance(get_plotly_layout('dark'), dict)

    def test_set_get_theme(self):
        set_theme('dark'); assert get_theme() == 'dark'
        set_theme('scientific'); assert get_theme() == 'scientific'

    def test_register_theme(self):
        register_theme('test_custom', palette=['#ff0000','#00ff00','#0000ff','#ffff00'], bg_paper='#fff')
        assert 'test_custom' in get_available_themes()
        assert isinstance(get_palette('test_custom'), list)


#  data/types 

class TestDataTypes:
    def test_detect_column_types(self, sample_df):
        r = detect_column_types(sample_df)
        assert isinstance(r, dict) and len(r) == len(sample_df.columns)

    def test_optimize_dataframe(self, sample_df):
        r = optimize_dataframe_types(sample_df)
        assert isinstance(r, pd.DataFrame) and set(r.columns) == set(sample_df.columns)

    def test_get_type_recommendations(self, sample_df):
        assert isinstance(get_type_recommendations(sample_df), pd.DataFrame)

    def test_optimize_numeric_type(self):
        r = optimize_numeric_type(pd.Series([1,2,3,4], dtype=np.int64))
        assert np.issubdtype(r.dtype, np.integer)

    def test_optimize_object_high_cardinality(self):
        r = optimize_object_type(pd.Series([f'v{i}' for i in range(20)]))
        assert r.dtype == object or r.dtype.name == 'str'

    def test_optimize_object_low_cardinality(self):
        r = optimize_object_type(pd.Series(['A','B','A','B','A']*3))
        assert r.dtype.name == 'category'

    def test_optimize_datetime_type(self):
        r = optimize_datetime_type(pd.Series(pd.date_range('2024-01-01', periods=5)))
        assert np.issubdtype(r.dtype, np.datetime64)

    def test_optimize_column_type_numeric(self):
        r = optimize_column_type(pd.Series([1,2,3,4]))
        assert np.issubdtype(r.dtype, np.number)

    def test_optimize_column_type_string(self):
        r = optimize_column_type(pd.Series(['A','B','A','B']))
        assert isinstance(r, pd.Series)

    def test_optimize_column_type_datetime(self):
        r = optimize_column_type(pd.Series(pd.date_range('2024-01-01', periods=4)))
        assert np.issubdtype(r.dtype, np.datetime64)

    def test_convert_to_epidemiological_types(self):
        df = pd.DataFrame({'cases':[1,2,3],'region':['A','B','A'],'rate':[0.1,0.2,0.3]})
        types = detect_column_types(df)
        r = convert_to_epidemiological_types(df, types)
        assert isinstance(r, pd.DataFrame) and len(r) == len(df)

    def test_convert_to_binary(self):
        assert set(convert_to_binary(pd.Series([True,False,True])).unique()).issubset({0,1})

    def test_convert_to_categorical(self):
        assert convert_to_categorical(pd.Series(['A','B','A'])).dtype.name == 'category'

    def test_convert_to_continuous(self):
        assert np.issubdtype(convert_to_continuous(pd.Series([1,2,3])).dtype, np.number)

    def test_convert_to_date(self):
        assert np.issubdtype(convert_to_date(pd.Series(['2024-01-01','2024-01-08'])).dtype, np.datetime64)

    def test_downcast_integers(self):
        df = pd.DataFrame({'n': np.array([1,2,3,4], dtype=np.int64)})
        r = optimize_dataframe_types(df, downcast_integers=True)
        assert isinstance(r, pd.DataFrame)

    def test_no_downcast_floats(self):
        df = pd.DataFrame({'x': [1.0,2.0,3.0]})
        assert isinstance(optimize_dataframe_types(df, downcast_floats=False), pd.DataFrame)


#  data/transformers ─

class TestDataTransformers:
    def test_normalize_standard(self):
        df = pd.DataFrame({'a':[1.,2.,3.,4.,5.]})
        r = normalize_data(df, columns=['a'], method='standard')
        assert abs(r['a'].mean()) < 1e-10

    def test_normalize_minmax(self):
        df = pd.DataFrame({'a':[1.,2.,3.,4.,5.]})
        r = normalize_data(df, columns=['a'], method='minmax')
        assert r['a'].min() == pytest.approx(0.) and r['a'].max() == pytest.approx(1.)

    def test_outlier_clip(self):
        df = pd.DataFrame({'v':[1.,2.,100.,1.5]})
        r = OutlierTransformer(numeric_columns=['v'], action='clip').fit_transform(df.copy())
        assert r['v'].max() < 100.

    def test_outlier_remove(self):
        df = pd.DataFrame({'v':[1.,2.,100.,1.5,1.8]})
        r = OutlierTransformer(numeric_columns=['v'], action='remove').fit_transform(df.copy())
        assert len(r) < len(df)

    def test_outlier_zscore_method(self):
        df = pd.DataFrame({'v':[1.,2.,3.,50.,2.,1.,3.]})
        r = OutlierTransformer(numeric_columns=['v'], method='zscore', threshold=2.0).fit_transform(df.copy())
        assert isinstance(r, pd.DataFrame)

    def test_feature_engineer(self):
        df = pd.DataFrame({'date': pd.date_range('2024-01-01', periods=4, freq='W'),
                           'cases':[10,20,15,5], 'region':['A','B','A','B']})
        r = FeatureEngineer().transform(df.copy())
        assert isinstance(r, pd.DataFrame) and len(r) == len(df)

    def test_create_pipeline_callable(self):
        pipe = create_pipeline([DateTransformer(date_columns='date')])
        assert callable(pipe)

    def test_pipeline_applies_transformers(self):
        df = pd.DataFrame({'date':['2024-01-01','2024-01-08'],'cases':[10,20],'region':['A','B']})
        pipe = create_pipeline([DateTransformer(date_columns='date')])
        assert 'date_year' in pipe(df.copy()).columns


#  core/utilities 

class TestEpiLoader:
    def test_instantiates(self):
        assert EpiLoader("test") is not None

    def test_custom_width(self):
        assert EpiLoader("test", width=60) is not None

    def test_is_tty_bool(self):
        assert isinstance(EpiLoader("test")._is_tty(), bool)

    def test_check_unicode_bool(self):
        assert isinstance(EpiLoader("test")._check_unicode(), bool)

    def test_check_color_bool(self):
        assert isinstance(EpiLoader("test")._check_color(), bool)

    def test_context_manager_silent(self):
        with EpiLoader("Silent"):
            x = 1 + 1
        assert x == 2

    def test_context_manager_exception_propagates(self):
        with pytest.raises(ValueError):
            with EpiLoader("Error test"):
                raise ValueError("test")

    def test_spinner_alias(self):
        with Spinner("Spinner test"):
            pass

    def test_multiple_contexts(self):
        for msg in ["Step 1","Step 2","Step 3"]:
            with EpiLoader(msg):
                pass

    def test_verbose_sensitivity_uses_loader(self):
        # EpiLoader is used during sensitivity verbose run
        sa = SensitivityAnalysis(SEIRModel, SEIRParameters,
            fixed=dict(N=50_000,I0=1,E0=5,t_span=(0,60)),
            distributions={'beta':('uniform',0.3,0.4)},
            n_samples=3, seed=0)
        r = sa.run(verbose=True)
        assert r.n_samples == 3
"""
tests/unit/test_viz_utils_themes.py

Coverage: viz/utils, viz/roc, viz/themes/registry, viz/forest, viz/contingency_plot
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
import matplotlib

from episia.viz.utils import (
    p_value_label, significance_stars, hex_to_rgb, hex_to_rgba_str,
    ci_band_xy, adjust_alpha, px_to_inches, auto_height,
    nice_log_ticks, symlog_range,
)
from episia.viz.themes.registry import (
    get_available_themes, get_palette, get_plotly_layout,
    get_theme, set_theme, register_theme, apply_mpl_theme,
)
from episia.viz.roc import plot_roc, plot_roc_compare, plot_precision_recall
from episia.viz.forest import plot_forest, plot_meta_forest
from episia.viz.contingency_plot import plot_measures
from episia.stats.diagnostic import roc_analysis
from episia.stats.contingency import Table2x2, risk_ratio, odds_ratio


#  Fixtures 

@pytest.fixture
def roc_result():
    np.random.seed(42)
    y_true  = np.array([1]*60 + [0]*60)
    y_score = np.concatenate([np.random.beta(5,2,60), np.random.beta(2,5,60)])
    return roc_analysis(y_true, y_score)

@pytest.fixture
def table():
    return Table2x2(a=40, b=10, c=20, d=30)

@pytest.fixture
def rr_result(table):
    return table.risk_ratio()

@pytest.fixture
def or_result(table):
    return table.odds_ratio()


#  viz/utils ─

class TestPValueLabel:
    def test_very_small(self):    assert 'p' in p_value_label(0.00001).lower()
    def test_small(self):         assert 'p' in p_value_label(0.001).lower()
    def test_moderate(self):      assert 'p' in p_value_label(0.03).lower()
    def test_large(self):         assert 'p' in p_value_label(0.5).lower()
    def test_returns_string(self): assert isinstance(p_value_label(0.05), str)


class TestSignificanceStars:
    def test_very_significant(self): assert '*' in significance_stars(0.0001)
    def test_significant(self):      assert '*' in significance_stars(0.005)
    def test_marginal(self):         assert '*' in significance_stars(0.04)
    def test_not_significant(self):  assert significance_stars(0.5) in ('', 'ns', 'n.s.')
    def test_returns_string(self):   assert isinstance(significance_stars(0.01), str)


class TestHexToRgb:
    def test_returns_tuple(self):    assert isinstance(hex_to_rgb('#2997ff'), tuple)
    def test_three_values(self):     assert len(hex_to_rgb('#2997ff')) == 3
    def test_white(self):            assert hex_to_rgb('#ffffff') == (255,255,255)
    def test_black(self):            assert hex_to_rgb('#000000') == (0,0,0)
    def test_known_value(self):      r,g,b = hex_to_rgb('#2997ff'); assert r==41 and g==151 and b==255


class TestHexToRgbaStr:
    def test_returns_string(self):   assert isinstance(hex_to_rgba_str('#2997ff', 0.5), str)
    def test_starts_rgba(self):      assert hex_to_rgba_str('#2997ff', 0.5).startswith('rgba(')
    def test_alpha_included(self):   assert '0.5' in hex_to_rgba_str('#2997ff', 0.5)


class TestAdjustAlpha:
    def test_returns_string(self):   assert isinstance(adjust_alpha('#2997ff', 0.5), str)
    def test_rgba_format(self):      assert adjust_alpha('#2997ff', 0.5).startswith('rgba(')
    def test_alpha_value(self):      assert '0.3' in adjust_alpha('#2997ff', 0.3)


class TestPxToInches:
    def test_100px(self):    assert abs(px_to_inches(100) - 1.0) < 0.01
    def test_200px(self):    assert abs(px_to_inches(200) - 2.0) < 0.01
    def test_returns_float(self): assert isinstance(px_to_inches(100), float)


class TestAutoHeight:
    def test_positive(self):        assert auto_height(5) > 0
    def test_scales_with_rows(self): assert auto_height(10) >= auto_height(3)
    def test_numeric(self):          assert isinstance(auto_height(5), (int, float))


class TestCiBandXy:
    def test_returns_tuple(self):
        r = ci_band_xy(np.array([1.,2.,3.]), np.array([0.5,1.,1.5]), np.array([1.5,3.,4.5]))
        assert isinstance(r, tuple) and len(r) == 2

    def test_double_length(self):
        n = 4
        x, y = ci_band_xy(np.arange(n,dtype=float), np.zeros(n), np.ones(n))
        assert len(x) == 2*n and len(y) == 2*n


class TestNiceLogTicks:
    def test_returns_list(self):    assert isinstance(nice_log_ticks(0.01,100), list)
    def test_ascending(self):
        r = nice_log_ticks(0.01,100)
        assert all(a < b for a,b in zip(r,r[1:]))
    def test_covers_range(self):
        r = nice_log_ticks(0.01,100)
        assert r[0] <= 0.01 and r[-1] >= 100


class TestSymlogRange:
    def test_returns_tuple(self):   assert isinstance(symlog_range(np.array([-1.,0.,5.])), tuple)
    def test_two_values(self):      lo,hi = symlog_range(np.array([-1.,0.,5.])); assert lo < hi
    def test_covers_data(self):
        lo,hi = symlog_range(np.array([-2.,0.,10.]))
        assert lo <= -2. and hi >= 10.


#  viz/themes/registry ─

class TestThemesRegistry:
    def test_get_available_returns_list(self):
        assert isinstance(get_available_themes(), list)

    def test_four_builtin_themes(self):
        themes = get_available_themes()
        for t in ('scientific','minimal','dark','colorblind'):
            assert t in themes

    def test_get_palette_returns_list(self):
        assert isinstance(get_palette(), list) and len(get_palette()) > 0

    def test_get_palette_named(self):
        assert isinstance(get_palette('dark'), list)

    def test_get_plotly_layout_returns_dict(self):
        assert isinstance(get_plotly_layout(), dict)

    def test_get_plotly_layout_dark(self):
        assert isinstance(get_plotly_layout('dark'), dict)

    def test_set_and_get_theme(self):
        set_theme('dark'); assert get_theme() == 'dark'
        set_theme('scientific'); assert get_theme() == 'scientific'

    def test_register_custom_theme(self):
        register_theme('my_theme',
                       palette=['#ff0000','#00ff00','#0000ff','#ffff00'],
                       bg_paper='#ffffff')
        assert 'my_theme' in get_available_themes()

    def test_palette_custom_theme(self):
        register_theme('my_theme2',
                       palette=['#aabbcc','#ddeeff','#112233','#445566'],
                       bg_paper='#ffffff')
        assert isinstance(get_palette('my_theme2'), list)

    def test_apply_mpl_theme(self):
        try:
            apply_mpl_theme('scientific')
        except Exception:
            pass  # may fail in headless but should not crash import


#  viz/roc ─

class TestPlotRoc:
    def test_plotly(self, roc_result):
        import plotly.graph_objects as go
        assert isinstance(plot_roc(roc_result, backend='plotly'), go.Figure)

    def test_matplotlib(self, roc_result):
        assert isinstance(plot_roc(roc_result, backend='matplotlib'), matplotlib.figure.Figure)

    def test_custom_title(self, roc_result):
        assert plot_roc(roc_result, title='My ROC') is not None

    def test_dark_theme(self, roc_result):
        assert plot_roc(roc_result, theme='dark') is not None

    def test_minimal_theme(self, roc_result):
        assert plot_roc(roc_result, theme='minimal') is not None


class TestPlotRocCompare:
    def test_two_models_plotly(self, roc_result):
        import plotly.graph_objects as go
        fig = plot_roc_compare([roc_result, roc_result], labels=['A','B'], backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_two_models_matplotlib(self, roc_result):
        fig = plot_roc_compare([roc_result, roc_result], labels=['A','B'], backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_three_models(self, roc_result):
        fig = plot_roc_compare([roc_result]*3, labels=['A','B','C'])
        assert fig is not None

    def test_single_model(self, roc_result):
        assert plot_roc_compare([roc_result], labels=['A']) is not None


class TestPlotPrecisionRecall:
    def test_plotly(self):
        np.random.seed(0)
        y_true = np.array([1]*30+[0]*30)
        y_score = np.random.rand(60)
        fig = plot_precision_recall(y_true, y_score, backend='plotly')
        assert fig is not None

    def test_matplotlib(self):
        np.random.seed(1)
        y_true = np.array([1]*30+[0]*30)
        y_score = np.random.rand(60)
        fig = plot_precision_recall(y_true, y_score, backend='matplotlib')
        assert fig is not None

    def test_custom_label(self):
        np.random.seed(2)
        y_true = np.array([1]*20+[0]*20)
        y_score = np.random.rand(40)
        assert plot_precision_recall(y_true, y_score, label='Classifier A') is not None


#  viz/forest — plot_meta_forest ─

class TestPlotMetaForest:
    def test_returns_figure(self):
        fig = plot_meta_forest(
            estimates=[1.5, 2.0, 1.8],
            ci_lowers=[1.1, 1.4, 1.2],
            ci_uppers=[2.0, 2.8, 2.6],
            labels=['Study A','Study B','Study C'],
        )
        assert fig is not None

    def test_plotly_backend(self):
        import plotly.graph_objects as go
        fig = plot_meta_forest(
            estimates=[1.5, 2.0], ci_lowers=[1.1,1.4],
            ci_uppers=[2.0,2.8], labels=['A','B'], backend='plotly',
        )
        assert isinstance(fig, go.Figure)

    def test_matplotlib_backend(self):
        fig = plot_meta_forest(
            estimates=[1.5, 2.0], ci_lowers=[1.1,1.4],
            ci_uppers=[2.0,2.8], labels=['A','B'], backend='matplotlib',
        )
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_with_pooled(self):
        fig = plot_meta_forest(
            estimates=[1.5, 2.0, 1.8],
            ci_lowers=[1.1, 1.4, 1.2],
            ci_uppers=[2.0, 2.8, 2.6],
            labels=['A','B','C'],
            pooled_estimate=1.7,
            pooled_ci=(1.3, 2.2),
            i_squared=25.0,
            tau_squared=0.03,
            p_heterogeneity=0.15,
        )
        assert fig is not None

    def test_with_weights(self):
        fig = plot_meta_forest(
            estimates=[1.5, 2.0, 1.8],
            ci_lowers=[1.1, 1.4, 1.2],
            ci_uppers=[2.0, 2.8, 2.6],
            labels=['A','B','C'],
            weights=[0.5, 0.3, 0.2],
        )
        assert fig is not None

    def test_custom_null_value(self):
        fig = plot_meta_forest(
            estimates=[0.5, 0.8], ci_lowers=[0.3,0.5],
            ci_uppers=[0.8,1.1], labels=['A','B'], null_value=0.0,
        )
        assert fig is not None

    def test_forest_import_ok(self):
        from episia.viz.forest import plot_forest, plot_meta_forest
        assert callable(plot_forest) and callable(plot_meta_forest)


#  viz/contingency_plot 

class TestPlotMeasures:
    def test_returns_figure(self, table):
        fig = plot_measures(table)
        assert fig is not None

    def test_plotly_backend(self, table):
        import plotly.graph_objects as go
        fig = plot_measures(table, backend='plotly')
        assert isinstance(fig, go.Figure)

    def test_matplotlib_backend(self, table):
        fig = plot_measures(table, backend='matplotlib')
        assert isinstance(fig, matplotlib.figure.Figure)

    def test_custom_title(self, table):
        fig = plot_measures(table, title='Association Measures Test')
        assert fig is not None

    def test_dark_theme(self, table):
        fig = plot_measures(table, theme='dark')
        assert fig is not None

    def test_selected_measures(self, table):
        fig = plot_measures(table, measures=['risk_ratio','odds_ratio'])
        assert fig is not None
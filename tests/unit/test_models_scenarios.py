"""
tests/test_models_scenarios.py
"""
import sys; sys.path.insert(0, '/tmp')
import pytest
import numpy as np
import pandas as pd
from episia.models import SEIRModel, SIRModel
from episia.models.parameters import SEIRParameters, SIRParameters, ScenarioSet
from episia.models.scenarios import ScenarioRunner, ScenarioResults


@pytest.fixture
def two_scenarios():
    return ScenarioSet([
        ("base",     SEIRParameters(N=100_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=1/14,t_span=(0,100))),
        ("reduced",  SEIRParameters(N=100_000,I0=1,E0=5,beta=0.18,sigma=1/5.2,gamma=1/14,t_span=(0,100))),
    ])

@pytest.fixture
def three_scenarios():
    return ScenarioSet([
        ("no_intervention", SEIRParameters(N=100_000,I0=1,E0=5,beta=0.35,sigma=1/5.2,gamma=1/14,t_span=(0,200))),
        ("moderate",        SEIRParameters(N=100_000,I0=1,E0=5,beta=0.22,sigma=1/5.2,gamma=1/14,t_span=(0,200))),
        ("strong",          SEIRParameters(N=100_000,I0=1,E0=5,beta=0.12,sigma=1/5.2,gamma=1/14,t_span=(0,200))),
    ])


class TestScenarioRunner:

    def test_init_stores_model_class(self, two_scenarios):
        runner = ScenarioRunner(SEIRModel)
        assert runner.model_class is SEIRModel

    def test_run_returns_scenario_results(self, two_scenarios):
        runner = ScenarioRunner(SEIRModel)
        result = runner.run(two_scenarios)
        assert isinstance(result, ScenarioResults)

    def test_run_two_scenarios_length(self, two_scenarios):
        runner = ScenarioRunner(SEIRModel)
        result = runner.run(two_scenarios)
        assert len(result) == 2

    def test_run_three_scenarios_length(self, three_scenarios):
        runner = ScenarioRunner(SEIRModel)
        result = runner.run(three_scenarios)
        assert len(result) == 3

    def test_iter_yields_results(self, two_scenarios):
        runner = ScenarioRunner(SEIRModel)
        result = runner.run(two_scenarios)
        items = list(result)
        assert len(items) == 2

    def test_sir_model_works(self):
        scenarios = ScenarioSet([
            ("a", SIRParameters(N=50_000,I0=5,beta=0.3,gamma=1/14,t_span=(0,100))),
            ("b", SIRParameters(N=50_000,I0=5,beta=0.15,gamma=1/14,t_span=(0,100))),
        ])
        runner = ScenarioRunner(SIRModel)
        result = runner.run(scenarios)
        assert len(result) == 2


class TestScenarioResults:

    def test_to_dataframe_returns_df(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

    def test_to_dataframe_has_r0(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert 'r0' in df.columns

    def test_to_dataframe_has_peak_infected(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert 'peak_infected' in df.columns

    def test_to_dataframe_has_final_size(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert 'final_size' in df.columns

    def test_to_dataframe_row_count(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert len(df) == 2

    def test_higher_beta_higher_r0(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        r0_base    = df.loc['base', 'r0']
        r0_reduced = df.loc['reduced', 'r0']
        assert r0_base > r0_reduced

    def test_higher_beta_higher_peak(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        df = result.to_dataframe()
        assert df.loc['base', 'peak_infected'] > df.loc['reduced', 'peak_infected']

    def test_three_scenarios_df_shape(self, three_scenarios):
        result = ScenarioRunner(SEIRModel).run(three_scenarios)
        df = result.to_dataframe()
        assert df.shape[0] == 3

    def test_plot_returns_figure(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        fig = result.plot(compartment='I')
        assert fig is not None

    def test_repr(self, two_scenarios):
        result = ScenarioRunner(SEIRModel).run(two_scenarios)
        r = repr(result)
        assert 'ScenarioResults' in r or '2' in r
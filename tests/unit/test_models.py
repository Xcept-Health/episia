"""
tests/unit/test_models.py
Unit tests for episia.models
    parameters : ModelParameters, SIRParameters, SEIRParameters,
                 SEIRDParameters, ScenarioSet
    solver     : solve_model, estimate_herd_immunity, doubling_time
    SIRModel   : construction, run, compartments, metrics, summary
    SEIRModel  : construction, run, compartments, metrics
    SEIRDModel : construction, run, compartments, mortality metrics
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from episia.models.parameters import (
    ModelParameters, SIRParameters, SEIRParameters,
    SEIRDParameters, ScenarioSet,
)
from episia.models.solver import (
    solve_model, estimate_herd_immunity, doubling_time,
)
from episia.models import SIRModel, SEIRModel, SEIRDModel
from episia.api.results import ModelResult



# Fixtures


@pytest.fixture
def sir_params():
    return SIRParameters(N=100_000, I0=10, beta=0.3, gamma=0.1, t_span=(0, 160))

@pytest.fixture
def seir_params():
    return SEIRParameters(
        N=100_000, I0=1, E0=10,
        beta=0.35, sigma=1/5.2, gamma=1/14,
        t_span=(0, 200),
    )

@pytest.fixture
def seird_params():
    return SEIRDParameters(
        N=100_000, I0=1, E0=5,
        beta=0.35, sigma=1/5.2, gamma=0.09, mu=0.01,
        t_span=(0, 200),
    )

@pytest.fixture
def sir_result(sir_params):
    return SIRModel(sir_params).run()

@pytest.fixture
def seir_result(seir_params):
    return SEIRModel(seir_params).run()

@pytest.fixture
def seird_result(seird_params):
    return SEIRDModel(seird_params).run()



# 1. ModelParameters (base)


class TestModelParameters:
    def test_valid(self):
        p = ModelParameters(N=1000, I0=10, t_span=(0, 100))
        assert p.N == 1000 and p.I0 == 10

    def test_s0_derived(self):
        p = ModelParameters(N=1000, I0=10, E0=5)
        assert p.S0 == pytest.approx(985.0)

    def test_n_zero_raises(self):
        with pytest.raises(ValueError, match="N must be"):
            ModelParameters(N=0, I0=0)

    def test_n_negative_raises(self):
        with pytest.raises(ValueError):
            ModelParameters(N=-100, I0=0)

    def test_i0_negative_raises(self):
        with pytest.raises(ValueError, match="I0"):
            ModelParameters(N=1000, I0=-1)

    def test_e0_negative_raises(self):
        with pytest.raises(ValueError, match="E0"):
            ModelParameters(N=1000, I0=0, E0=-1)

    def test_compartments_exceed_n_raises(self):
        with pytest.raises(ValueError, match="exceeds N"):
            ModelParameters(N=100, I0=80, E0=80)

    def test_invalid_t_span_raises(self):
        with pytest.raises(ValueError, match="t_span"):
            ModelParameters(N=1000, I0=1, t_span=(100, 0))

    def test_equal_t_span_raises(self):
        with pytest.raises(ValueError, match="t_span"):
            ModelParameters(N=1000, I0=1, t_span=(50, 50))

    def test_to_dict_keys(self):
        p = ModelParameters(N=1000, I0=10)
        d = p.to_dict()
        for k in ["N", "I0", "t_span"]:
            assert k in d



# 2. SIRParameters


class TestSIRParameters:
    def test_valid(self, sir_params):
        assert sir_params.beta == 0.3 and sir_params.gamma == 0.1

    def test_r0(self, sir_params):
        assert sir_params.r0 == pytest.approx(3.0)

    def test_t_infectious(self, sir_params):
        assert sir_params.t_infectious == pytest.approx(10.0)

    def test_beta_zero_raises(self):
        with pytest.raises(ValueError, match="beta"):
            SIRParameters(N=1000, I0=1, beta=0.0, gamma=0.1)

    def test_beta_negative_raises(self):
        with pytest.raises(ValueError, match="beta"):
            SIRParameters(N=1000, I0=1, beta=-0.1, gamma=0.1)

    def test_gamma_zero_raises(self):
        with pytest.raises(ValueError, match="gamma"):
            SIRParameters(N=1000, I0=1, beta=0.3, gamma=0.0)

    def test_to_dict_has_r0(self, sir_params):
        assert "r0" in sir_params.to_dict()

    def test_s0(self, sir_params):
        assert sir_params.S0 == pytest.approx(100_000 - 10)



# 3. SEIRParameters


class TestSEIRParameters:
    def test_valid(self, seir_params):
        assert seir_params.beta == pytest.approx(0.35)

    def test_r0(self, seir_params):
        # R0 = beta/gamma = 0.35/(1/14) = 4.9
        assert seir_params.r0 == pytest.approx(4.9)

    def test_t_incubation(self, seir_params):
        assert seir_params.t_incubation == pytest.approx(5.2)

    def test_t_infectious(self, seir_params):
        assert seir_params.t_infectious == pytest.approx(14.0)

    def test_sigma_zero_raises(self):
        with pytest.raises(ValueError, match="sigma"):
            SEIRParameters(N=1000, I0=1, beta=0.3, sigma=0.0, gamma=0.1)

    def test_to_dict_has_sigma(self, seir_params):
        assert "sigma" in seir_params.to_dict()

    def test_s0_accounts_for_e0(self, seir_params):
        assert seir_params.S0 == pytest.approx(100_000 - 1 - 10)



# 4. SEIRDParameters


class TestSEIRDParameters:
    def test_valid(self, seird_params):
        assert seird_params.mu == pytest.approx(0.01)

    def test_r0(self, seird_params):
        # R0 = beta/(gamma+mu) = 0.35/0.1 = 3.5
        assert seird_params.r0 == pytest.approx(3.5)

    def test_cfr(self, seird_params):
        # CFR = mu/(gamma+mu) = 0.01/0.10 = 0.1
        assert seird_params.cfr == pytest.approx(0.1)

    def test_mu_negative_raises(self):
        with pytest.raises(ValueError, match="mu"):
            SEIRDParameters(N=1000, I0=1, beta=0.3, sigma=0.2,
                            gamma=0.09, mu=-0.01)

    def test_mu_zero_allowed(self):
        # mu=0 → SEIRD degenerates to SEIR
        p = SEIRDParameters(N=1000, I0=1, beta=0.3, sigma=0.2,
                            gamma=0.1, mu=0.0)
        assert p.cfr == pytest.approx(0.0)

    def test_to_dict_has_cfr(self, seird_params):
        assert "cfr" in seird_params.to_dict()



# 5. ScenarioSet


class TestScenarioSet:
    def test_empty(self):
        s = ScenarioSet()
        assert len(s) == 0

    def test_add_scenario(self, sir_params):
        s = ScenarioSet()
        s.add("baseline", sir_params)
        assert len(s) == 1

    def test_init_with_list(self, sir_params):
        s = ScenarioSet([("base", sir_params)])
        assert len(s) == 1

    def test_labels(self, sir_params):
        s = ScenarioSet([("A", sir_params), ("B", sir_params)])
        assert s.labels() == ["A", "B"]

    def test_iter(self, sir_params):
        s = ScenarioSet([("A", sir_params)])
        for label, params in s:
            assert label == "A"
            assert isinstance(params, SIRParameters)

    def test_chaining(self, sir_params):
        s = ScenarioSet()
        result = s.add("A", sir_params).add("B", sir_params)
        assert result is s
        assert len(s) == 2

    def test_repr(self, sir_params):
        s = ScenarioSet([("X", sir_params)])
        assert "ScenarioSet" in repr(s)
        assert "1" in repr(s)



# 6. solver utilities


class TestSolverUtils:
    def test_estimate_hit_r0_two(self):
        # HIT = 1 - 1/2 = 0.5
        assert estimate_herd_immunity(2.0) == pytest.approx(0.5)

    def test_estimate_hit_r0_four(self):
        # HIT = 1 - 1/4 = 0.75
        assert estimate_herd_immunity(4.0) == pytest.approx(0.75)

    def test_estimate_hit_r0_below_one(self):
        # R0 < 1 → no herd immunity needed
        assert estimate_herd_immunity(0.8) == pytest.approx(0.0)

    def test_estimate_hit_r0_one(self):
        assert estimate_herd_immunity(1.0) == pytest.approx(0.0)

    def test_estimate_hit_zero_raises(self):
        with pytest.raises(ValueError):
            estimate_herd_immunity(0.0)

    def test_estimate_hit_negative_raises(self):
        with pytest.raises(ValueError):
            estimate_herd_immunity(-1.0)

    def test_doubling_time_nominal(self):
        # T2 = ln(2)/(0.3-0.1) = ln(2)/0.2 ≈ 3.466
        dt = doubling_time(0.3, 0.1)
        assert dt == pytest.approx(math.log(2) / 0.2)

    def test_doubling_time_no_growth_raises(self):
        with pytest.raises(ValueError):
            doubling_time(0.1, 0.3)   # beta < gamma

    def test_doubling_time_equal_raises(self):
        with pytest.raises(ValueError):
            doubling_time(0.2, 0.2)

    def test_solve_model_basic(self):
        # Disable conservation check (decay is not a conservative system)
        def simple_decay(t, y): return [-0.1 * y[0]]
        t, sol = solve_model(simple_decay, np.array([1.0]), (0, 10),
                             check_conservation=False)
        assert len(t) > 0
        assert sol.shape[0] == 1
        # Exponential decay: y(10) ≈ e^{-1} ≈ 0.368
        assert sol[0, -1] == pytest.approx(math.exp(-1.0), rel=0.01)

    def test_solve_model_conservation(self, sir_params):
        model = SIRModel(sir_params)
        t, sol = solve_model(
            model._derivatives,
            model._initial_state(),
            sir_params.t_span,
        )
        # S + I + R should stay ≈ N
        total = sol.sum(axis=0)
        assert np.allclose(total, sir_params.N, rtol=1e-3)



# 7. SIRModel


class TestSIRModel:
    def test_wrong_param_type_raises(self):
        with pytest.raises(TypeError):
            SIRModel(SEIRParameters(N=1000, I0=1, beta=0.3,
                                    sigma=0.2, gamma=0.1))

    def test_repr_before_run(self, sir_params):
        m = SIRModel(sir_params)
        assert "ready" in repr(m)

    def test_repr_after_run(self, sir_params):
        m = SIRModel(sir_params)
        m.run()
        assert "solved" in repr(m)

    def test_run_returns_model_result(self, sir_params):
        assert isinstance(SIRModel(sir_params).run(), ModelResult)

    def test_compartment_names(self, sir_params):
        assert SIRModel(sir_params).compartment_names == ["S", "I", "R"]

    def test_compartments_in_result(self, sir_result):
        for c in ["S", "I", "R"]:
            assert c in sir_result.compartments

    def test_model_type(self, sir_result):
        assert sir_result.model_type == "SIR"

    def test_t_array_length(self, sir_result):
        assert len(sir_result.t) >= 500

    def test_t_starts_at_zero(self, sir_result):
        assert sir_result.t[0] == pytest.approx(0.0)

    def test_t_ends_at_t_end(self, sir_result, sir_params):
        assert sir_result.t[-1] == pytest.approx(sir_params.t_span[1])

    def test_population_conserved(self, sir_result, sir_params):
        S = sir_result.compartments["S"]
        I = sir_result.compartments["I"]
        R = sir_result.compartments["R"]
        total = S + I + R
        assert np.allclose(total, sir_params.N, rtol=1e-3)

    def test_all_compartments_non_negative(self, sir_result):
        for name, arr in sir_result.compartments.items():
            assert np.all(arr >= -1e-6), f"{name} has negative values"

    def test_s_monotone_decreasing(self, sir_result):
        S = sir_result.compartments["S"]
        assert np.all(np.diff(S) <= 1e-6)

    def test_r_monotone_increasing(self, sir_result):
        R = sir_result.compartments["R"]
        assert np.all(np.diff(R) >= -1e-6)

    def test_r0_positive(self, sir_result):
        assert sir_result.r0 > 0

    def test_r0_value(self, sir_result, sir_params):
        assert sir_result.r0 == pytest.approx(sir_params.r0)

    def test_peak_infected_positive(self, sir_result):
        assert sir_result.peak_infected > 0

    def test_peak_time_in_range(self, sir_result, sir_params):
        assert sir_params.t_span[0] < sir_result.peak_time < sir_params.t_span[1]

    def test_final_size_between_0_and_1(self, sir_result):
        assert 0 < sir_result.final_size <= 1

    def test_to_dataframe(self, sir_params):
        df = SIRModel(sir_params).run().to_dataframe()
        assert "t" in df.columns
        for c in ["S", "I", "R"]:
            assert c in df.columns

    def test_summary_keys(self, sir_params):
        m = SIRModel(sir_params)
        s = m.summary()
        for k in ["model", "r0", "peak_infected", "peak_time", "final_size"]:
            assert k in s

    def test_summary_auto_runs(self, sir_params):
        m = SIRModel(sir_params)
        assert m._result is None
        m.summary()
        assert m._result is not None

    def test_i_peak_less_than_n(self, sir_result, sir_params):
        assert sir_result.peak_infected < sir_params.N

    def test_high_r0_large_final_size(self):
        p = SIRParameters(N=100_000, I0=10, beta=0.9, gamma=0.1, t_span=(0, 200))
        r = SIRModel(p).run()
        assert r.final_size > 0.8   # R0=9, most of population infected



# 8. SEIRModel


class TestSEIRModel:
    def test_wrong_param_type_raises(self, sir_params):
        with pytest.raises(TypeError):
            SEIRModel(sir_params)

    def test_run_returns_model_result(self, seir_params):
        assert isinstance(SEIRModel(seir_params).run(), ModelResult)

    def test_compartment_names(self, seir_params):
        assert SEIRModel(seir_params).compartment_names == ["S", "E", "I", "R"]

    def test_compartments_in_result(self, seir_result):
        for c in ["S", "E", "I", "R"]:
            assert c in seir_result.compartments

    def test_model_type(self, seir_result):
        assert seir_result.model_type == "SEIR"

    def test_population_conserved(self, seir_result, seir_params):
        S = seir_result.compartments["S"]
        E = seir_result.compartments["E"]
        I = seir_result.compartments["I"]
        R = seir_result.compartments["R"]
        total = S + E + I + R
        assert np.allclose(total, seir_params.N, rtol=1e-3)

    def test_all_compartments_non_negative(self, seir_result):
        for name, arr in seir_result.compartments.items():
            assert np.all(arr >= -1e-6), f"{name} has negative values"

    def test_e_starts_at_e0(self, seir_result, seir_params):
        assert seir_result.compartments["E"][0] == pytest.approx(
            seir_params.E0, rel=0.01)

    def test_s_monotone_decreasing(self, seir_result):
        S = seir_result.compartments["S"]
        assert np.all(np.diff(S) <= 1e-6)

    def test_r_monotone_increasing(self, seir_result):
        R = seir_result.compartments["R"]
        assert np.all(np.diff(R) >= -1e-6)

    def test_r0_value(self, seir_result, seir_params):
        assert seir_result.r0 == pytest.approx(seir_params.r0)

    def test_peak_infected_positive(self, seir_result):
        assert seir_result.peak_infected > 0

    def test_peak_time_later_than_sir(self):
        """SEIR peak comes later than SIR due to incubation delay."""
        sir_p = SIRParameters(N=100_000, I0=10, beta=0.3, gamma=0.1,
                               t_span=(0, 300))
        seir_p = SEIRParameters(N=100_000, I0=10, E0=0, beta=0.3,
                                 sigma=0.2, gamma=0.1, t_span=(0, 300))
        sir_r  = SIRModel(sir_p).run()
        seir_r = SEIRModel(seir_p).run()
        assert seir_r.peak_time > sir_r.peak_time

    def test_to_dataframe_columns(self, seir_params):
        df = SEIRModel(seir_params).run().to_dataframe()
        for c in ["t", "S", "E", "I", "R"]:
            assert c in df.columns

    def test_herd_immunity_threshold_stored(self, seir_result):
        # result should have r0 from which HIT can be derived
        r0 = seir_result.r0
        hit = 1.0 - 1.0 / r0
        assert 0 < hit < 1



# 9. SEIRDModel


class TestSEIRDModel:
    def test_wrong_param_type_raises(self, sir_params):
        with pytest.raises(TypeError):
            SEIRDModel(sir_params)

    def test_run_returns_model_result(self, seird_params):
        assert isinstance(SEIRDModel(seird_params).run(), ModelResult)

    def test_compartment_names(self, seird_params):
        assert SEIRDModel(seird_params).compartment_names == ["S","E","I","R","D"]

    def test_compartments_in_result(self, seird_result):
        for c in ["S", "E", "I", "R", "D"]:
            assert c in seird_result.compartments

    def test_model_type(self, seird_result):
        assert seird_result.model_type == "SEIRD"

    def test_population_conserved(self, seird_result, seird_params):
        S = seird_result.compartments["S"]
        E = seird_result.compartments["E"]
        I = seird_result.compartments["I"]
        R = seird_result.compartments["R"]
        D = seird_result.compartments["D"]
        total = S + E + I + R + D
        assert np.allclose(total, seird_params.N, rtol=1e-3)

    def test_all_compartments_non_negative(self, seird_result):
        for name, arr in seird_result.compartments.items():
            assert np.all(arr >= -1e-6), f"{name} has negative values"

    def test_d_monotone_increasing(self, seird_result):
        D = seird_result.compartments["D"]
        assert np.all(np.diff(D) >= -1e-6)

    def test_d_starts_near_zero(self, seird_result, seird_params):
        assert seird_result.compartments["D"][0] == pytest.approx(
            seird_params.D0, abs=1.0)

    def test_total_deaths_positive(self, seird_result):
        assert seird_result.compartments["D"][-1] > 0

    def test_r0_value(self, seird_result, seird_params):
        assert seird_result.r0 == pytest.approx(seird_params.r0)

    def test_deaths_less_than_n(self, seird_result, seird_params):
        assert seird_result.compartments["D"][-1] < seird_params.N

    def test_mu_zero_no_deaths(self):
        p = SEIRDParameters(N=100_000, I0=1, E0=5,
                             beta=0.35, sigma=1/5.2, gamma=0.09, mu=0.0,
                             t_span=(0, 200))
        r = SEIRDModel(p).run()
        assert r.compartments["D"][-1] == pytest.approx(0.0, abs=1.0)

    def test_higher_mu_more_deaths(self, seird_params):
        p_low  = SEIRDParameters(N=100_000, I0=1, E0=5,
                                  beta=0.35, sigma=1/5.2,
                                  gamma=0.09, mu=0.005, t_span=(0, 200))
        p_high = SEIRDParameters(N=100_000, I0=1, E0=5,
                                  beta=0.35, sigma=1/5.2,
                                  gamma=0.09, mu=0.05,  t_span=(0, 200))
        d_low  = SEIRDModel(p_low).run().compartments["D"][-1]
        d_high = SEIRDModel(p_high).run().compartments["D"][-1]
        assert d_high > d_low



# 10. Cross-model epidemiological properties


class TestEpidemiologicalProperties:
    def test_higher_beta_larger_final_size(self):
        p1 = SIRParameters(N=100_000, I0=10, beta=0.2, gamma=0.1, t_span=(0,300))
        p2 = SIRParameters(N=100_000, I0=10, beta=0.4, gamma=0.1, t_span=(0,300))
        r1 = SIRModel(p1).run()
        r2 = SIRModel(p2).run()
        assert r2.final_size > r1.final_size

    def test_higher_gamma_smaller_final_size(self):
        p1 = SIRParameters(N=100_000, I0=10, beta=0.3, gamma=0.05, t_span=(0,400))
        p2 = SIRParameters(N=100_000, I0=10, beta=0.3, gamma=0.2,  t_span=(0,400))
        r1 = SIRModel(p1).run()
        r2 = SIRModel(p2).run()
        assert r1.final_size > r2.final_size

    def test_r0_less_than_1_no_epidemic(self):
        p = SIRParameters(N=100_000, I0=10, beta=0.05, gamma=0.1, t_span=(0,300))
        r = SIRModel(p).run()
        # R0=0.5 < 1, infectious should decrease from start
        I = r.compartments["I"]
        assert I[-1] < I[0]

    def test_hit_equals_1_minus_s_final(self):
        """At end of epidemic S/N ≈ 1 - final_size, verify consistency."""
        p = SIRParameters(N=100_000, I0=10, beta=0.3, gamma=0.1, t_span=(0,400))
        r = SIRModel(p).run()
        s_final_fraction = r.compartments["S"][-1] / p.N
        assert s_final_fraction == pytest.approx(1 - r.final_size, abs=0.01)

    def test_seir_final_size_less_than_n(self, seir_result, seir_params):
        assert seir_result.final_size < 1.0
        assert seir_result.final_size * seir_params.N > 0

    def test_seird_r_plus_d_equals_attack_rate(self, seird_result, seird_params):
        R = seird_result.compartments["R"][-1]
        D = seird_result.compartments["D"][-1]
        attack = (R + D) / seird_params.N
        assert 0 < attack < 1
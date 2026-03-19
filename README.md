<div align="center">

```
███████╗██████╗ ██╗███████╗██╗ █████╗
 ██╔════╝██╔══██╗██║██╔════╝██║██╔══██╗
 █████╗  ██████╔╝██║███████╗██║███████║
 ██╔══╝  ██╔═══╝ ██║╚════██║██║██╔══██║
 ███████╗██║     ██║███████║██║██║  ██║
 ╚══════╝╚═╝     ╚═╝╚══════╝╚═╝╚═╝  ╚═╝
```

**Open-source epidemiology & biostatistics for Python**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.0a1-orange?style=flat-square)](https://github.com/Xcept-Health/episia)
[![Status](https://img.shields.io/badge/Status-Alpha-yellow?style=flat-square)](https://github.com/Xcept-Health/episia/releases)
[![Organization](https://img.shields.io/badge/Xcept--Health-Burkina%20Faso-purple?style=flat-square)](https://xcept-health.com)
[![Tests](https://img.shields.io/badge/Tests-1390%20passed-brightgreen?style=flat-square)](#test-coverage)
[![Coverage](https://img.shields.io/badge/Coverage-80%25-brightgreen?style=flat-square)](#test-coverage)
[![Validation](https://img.shields.io/badge/Validation-OpenEpi-brightgreen?style=flat-square)](examples/episia_vs_openepi.ipynb)

*epi- (Greek: upon, over, the root of epidemiology) · -sia (African geographic context)*

[Installation](#installation) · [Quick Start](#quick-start) · [Modules](#modules) · [Citation](#citation) · [Roadmap](#roadmap)

</div>

---

## Overview

Episia is a Python library for epidemiologists, public health researchers, and biostatisticians. It provides a unified, validated set of tools covering the full analytical workflow from raw surveillance data to statistical analysis, epidemic modeling, and automated report generation.

Built on the scientific foundation of [OpenEpi](https://openepi.com), Episia extends it with compartmental epidemic models (SIR/SEIR/SEIRD), Monte Carlo sensitivity analysis, and a modern Python API designed to be both approachable and production-grade.

**Designed for:**

- Field epidemiologists and biostatisticians working in resource-limited settings
- Public health researchers in Africa and around the world
- Students and academics in epidemiology and biostatistics
- Developers building health analytics applications

**Key properties:**

- 100% offline zero network dependencies at runtime
- Dual visualization backend: Plotly (interactive) and Matplotlib (publication-quality)
- Unified result objects: every function returns a rich, serializable result
- Self-contained HTML reports with dark/light mode toggle
- Terminal loader animation for long-running operations (`EpiLoader`)
- Systematic validation against OpenEpi reference implementation
- Jupiter notebook support

---

## Validation

Episia is systematically validated against [OpenEpi](https://openepi.com), the reference in epidemiology. All results from core functions (risk ratio, odds ratio, confidence intervals, χ² tests, etc.) have been compared and agree with OpenEpi on standard datasets.

**[Check out the full validation notebook](https://github.com/Xcept-Health/episia/blob/main/examples/episia_vs_openepi.ipynb)** 

This notebook reproduces OpenEpi's calculations step by step and demonstrates concordance.

---

## Installation

```bash
# Standard install
pip install episia

# Development install (editable)
git clone https://github.com/Xcept-Health/episia.git
cd episia
pip install -e .

# With all optional dependencies
pip install episia[full]
```

**Optional extras:**

| Extra | What it adds |
|---|---|
| `pip install episia[full]` | ipywidgets, kaleido, scikit-learn, seaborn, openpyxl |
| `pip install episia[jupyter]` | Jupyter + interactive widgets |
| `pip install episia[export]` | PNG/SVG/PDF export via kaleido |
| `pip install episia[dev]` | pytest, black, mypy, pre-commit |

**Python 3.9+ required.** Core dependencies: `numpy`, `scipy`, `pandas`, `plotly`, `matplotlib`.

---

## Quick Start

```python
from episia import epi

# Epidemic model
model  = epi.seir(N=1_000_000, I0=10, E0=50,
                  beta=0.35, sigma=1/5.2, gamma=1/14)
result = model.run()
print(result)
# SEIR Model
#   R0            : 4.900
#   Peak infected : 331,751  at t=84.5
#   Final size    : 99.2%
#   Duration      : 0-365

result.plot().show()  # Opens interactive Plotly figure in browser

# Biostatistics
rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
print(rr)
# Risk Ratio: 2.667 (1.514-4.696)

# Automated report
import webbrowser, os
report = epi.report(result, title="SEIR Burkina Faso 2024")
path   = report.save_html("report.html")
webbrowser.open(f"file:///{os.path.abspath(path)}")
```

**Terminal loader for long operations:**

```python
from episia.core.utilities import EpiLoader

with EpiLoader("Running SEIR model"):
    result = model.run()
```

**Quick reference from the terminal:**

```bash
python -m episia
```

---

## Modules

### `episia.models` – Compartmental epidemic models

| Class / Function | Description |
|---|---|
| `SIRModel` | Classic SIRdS/dt, dI/dt, dR/dt |
| `SEIRModel` | SEIR with latent (exposed) compartment |
| `SEIRDModel` | SEIRD with disease-induced mortality |
| `ModelCalibrator` | Fit model parameters to observed data (L-BFGS-B) |
| `SensitivityAnalysis` | Monte Carlo parameter uncertainty analysis |
| `ScenarioRunner` | Multi-scenario comparison with envelope plots |

```python
from episia.models import SEIRModel, SEIRDModel, SensitivityAnalysis
from episia.models.parameters import SEIRParameters, SEIRDParameters, ScenarioSet

# SEIR-COVID-like parameters
params = SEIRParameters(
    N=1_000_000, I0=1, E0=10,
    beta=0.35,
    sigma=1/5.2,    # 1 / incubation period (days)
    gamma=1/14,     # 1 / infectious period (days)
    t_span=(0, 365),
)
result = SEIRModel(params).run()

# SEIRD-with mortality
params_d = SEIRDParameters(
    N=1_000_000, I0=1, E0=10,
    beta=0.35, sigma=1/5.2, gamma=0.09, mu=0.01,  # CFR ~10%
)
result_d = SEIRDModel(params_d).run()
print(f"Total deaths: {result_d.compartments['D'][-1]:,.0f}")

# Monte Carlo sensitivity analysis
sa = SensitivityAnalysis(
    model_class=SEIRModel,
    param_class=SEIRParameters,
    fixed=dict(N=1_000_000, I0=10, E0=50, t_span=(0, 365)),
    distributions={
        "beta":  ("uniform",    0.25, 0.50),
        "sigma": ("normal",     1/5.2, 0.02),
        "gamma": ("triangular", 1/21, 1/14, 1/7),
    },
    n_samples=500,
    seed=42,
)
sa_result = sa.run()
sa_result.plot("I").show()
sa_result.plot_metric_distribution("r0").show()
print(sa_result.summary())

# Scenario comparison
scenarios = ScenarioSet([
    ("No intervention", SEIRParameters(N=1_000_000, I0=10, E0=50, beta=0.35, sigma=1/5.2, gamma=1/14)),
    ("50% reduction",   SEIRParameters(N=1_000_000, I0=10, E0=50, beta=0.18, sigma=1/5.2, gamma=1/14)),
    ("70% reduction",   SEIRParameters(N=1_000_000, I0=10, E0=50, beta=0.11, sigma=1/5.2, gamma=1/14)),
])
from episia.models import ScenarioRunner
sr = ScenarioRunner(SEIRModel).run(scenarios)
sr.plot(compartment="I").show()
sr.to_dataframe()
```

---

### `episia.stats` – Biostatistics & epidemiological measures

| Function | Returns | Description |
|---|---|---|
| `risk_ratio(a, b, c, d)` | `AssociationResult` | Risk ratio with CI |
| `odds_ratio(a, b, c, d)` | `AssociationResult` | Odds ratio with CI |
| `proportion_ci(k, n)` | `ProportionResult` | ProportionWilson, Wald, Jeffreys, Clopper-Pearson, Agresti-Coull |
| `mean_ci(data)` | `MeanResult` | Mean with t / normal CI |
| `incidence_rate(cases, person_time)` | `dict` | Incidence rateByar + exact Poisson CI |
| `diagnostic_test_2x2(tp, fp, fn, tn)` | `DiagnosticResult` | Sensitivity, specificity, PPV, NPV, LR+/- |
| `roc_analysis(y_true, y_score)` | `ROCResult` | Full ROC curve, AUC, optimal threshold (Youden) |
| `sample_size_risk_ratio(...)` | `SampleSizeResult` | Sample size for cohort study |
| `sample_size_single_proportion(...)` | `SampleSizeResult` | Sample size for prevalence survey |
| `mantel_haenszel_or(strata)` | `StratifiedResult` | Pooled OR/RR with Cochran Q, I² |
| `logistic_regression(X, y)` | `RegressionResult` | Logistic regressionIRLS |
| `poisson_regression(X, y)` | `RegressionResult` | Poisson regression with offset support |

```python
from episia.stats import (
    risk_ratio, odds_ratio, proportion_ci,
    diagnostic_test_2x2, roc_analysis,
    sample_size_risk_ratio,
)

# Association measures
rr = risk_ratio(a=40, b=10, c=20, d=30)
print(rr)               # Risk Ratio: 2.667 (1.514-4.696)
print(rr.significant)   # True
print(rr.p_value)

or_ = odds_ratio(a=40, b=10, c=20, d=30)
print(or_)              # Odds Ratio: 6.000 (2.453-14.678)

# Proportions5 CI methods
p = proportion_ci(k=45, n=200, method="wilson")
print(p)                # Proportion: 0.2250 (0.1714-0.2888)

# Diagnostic test evaluation
diag = diagnostic_test_2x2(tp=80, fp=10, fn=20, tn=90)
print(diag)
# Sensitivity : 0.800
# Specificity : 0.900
# PPV         : 0.889   NPV: 0.818
# LR+         : 8.000   LR-: 0.222
# Accuracy    : 0.850   Youden: 0.700

# ROC curve
import numpy as np
y_true  = np.array([1,1,1,0,0,0,1,0,1,0])
y_score = np.array([0.9,0.8,0.7,0.3,0.2,0.1,0.6,0.4,0.85,0.35])
roc = roc_analysis(y_true, y_score)
print(f"AUC: {roc.auc:.3f}")
roc.plot().show()

# Sample size
ss = sample_size_risk_ratio(rr_expected=2.0, p0=0.10, alpha=0.05, power=0.80)
print(ss)
# Sample SizeCohort Study
#   Per group : 199
#   Total     : 398
#   Power     : 80.0%  alpha=0.05

# Stratified analysis
from episia.stats.stratified import mantel_haenszel_or
from episia.stats.contingency import Table2x2

strata = [
    Table2x2(15, 5, 25, 20),   # < 5 years
    Table2x2(30, 10, 40, 35),  # 5-14 years
    Table2x2(20, 8, 30, 25),   # 15+ years
]
mh = mantel_haenszel_or(strata)
print(mh)
```

---

### `episia.viz` – Visualization

All plot functions accept `backend="plotly"` (default, interactive) or `backend="matplotlib"` (publication-quality, 300 DPI).

Available themes: `scientific`, `minimal`, `dark`, `colorblind`.

```python
import numpy as np
from episia import epi
from episia.viz import plot_epicurve, set_theme, get_available_themes
from episia.stats.diagnostic import roc_analysis
from episia.api.results import TimeSeriesResult
from episia.core.utilities import EpiLoader

print("Available themes:", get_available_themes())
set_theme("dark")

with EpiLoader("Running SEIR model"):
    result = epi.seir(N=1_000_000, I0=10, E0=50,
                      beta=0.35, sigma=1/5.2, gamma=1/14).run()

# Epidemic curveanimated, capped at 60 frames
with EpiLoader("Building epidemic curve"):
    ts = TimeSeriesResult(times=result.t, values=result.compartments["I"])
    fig_curve = plot_epicurve(ts, animate=True)
fig_curve.show()

# ROC curve
with EpiLoader("Computing ROC curve"):
    y_true  = np.array([1,1,1,0,0,0,1,0,1,0])
    y_score = np.array([0.9,0.8,0.7,0.3,0.2,0.1,0.6,0.4,0.85,0.35])
    roc_result = roc_analysis(y_true, y_score)
roc_result.plot().show()

# Model trajectories
result.plot().show()

# Matplotlib exportpublication-quality
fig = result.plot(backend="matplotlib")
fig.savefig("figure1.pdf", dpi=300, bbox_inches="tight")

# Interactive HTML export
result.plot().write_html("figure1.html")
```

---

### `episia.data` – Surveillance data

```python
from episia.data import SurveillanceDataset, AlertEngine
from episia.viz import plot_epicurve

# Load from CSV (DHIS2-compatible export)
ds = SurveillanceDataset.from_csv(
    "meningitis_2024.csv",
    date_col="date",
    cases_col="cases",
    deaths_col="deaths",
    district_col="district",
    population_col="population",
)

print(ds)
# SurveillanceDataset(n=260, cases=1036, 2024-01-01 to 2024-12-23)

print(ds.summary())

# Attack rate per 100,000
ar = ds.attack_rate(population=500_000, per=100_000)

# Weekly aggregation
weekly = ds.aggregate(freq="W")

# Endemic channel (historical percentile envelope)
channel = ds.endemic_channel(percentiles=(25, 50, 75))

# Alert detectionthreshold, z-score, endemic channel
engine  = AlertEngine(ds)
alerts  = engine.run(threshold=15, zscore_threshold=2.0, use_endemic_channel=True)
summary = engine.alert_summary(alerts)
print(f"{summary['n_alerts']} alerts: {summary['severity_counts']}")

# Epidemic curve
ts = ds.to_timeseries_result()
plot_epicurve(ts, title="MeningitisCentre Region 2024").show()
```

---

### `episia.dhis2` – DHIS2 Integration

Pull surveillance data directly from a DHIS2 instance (health ministry reporting system).

```python
from episia.dhis2 import DHIS2Client, DHIS2Adapter
from episia.data import SurveillanceDataset
from episia.core.utilities import EpiLoader
from episia import epi

# Initialize DHIS2 client
client = DHIS2Client(
    base_url="https://dhis2.moh.gov.bf",  # Burkina Faso example
    username="epi_officer",
    password="your_password",  # Use environment variable in production
)

# Verify connection
print(client.about())  # Prints DHIS2 version, instance info

with EpiLoader("Fetching meningitis data from DHIS2"):
    # Get all meningitis cases from 2024
    cases_data = client.get_data_values(
        data_element="rQLFQyPSmie",  # Meningitis confirmed cases (example UID)
        period="202401:202412",      # Jan-Dec 2024
        org_units="ImspD0yaksKo",    # All facilities under Centre Region (UID)
    )

# Transform to epidemiological dataset
adapter = DHIS2Adapter()
ds = adapter.to_surveillance_dataset(
    cases_data,
    date_col="period",
    cases_col="value",
    location_col="orgUnit",
    population_col=None,  # Load from separate API call
)

print(ds)
# SurveillanceDataset(n=156, cases=342, 2024-01-01 to 2024-12-31)

# Analyze trends
weekly = ds.aggregate(freq="W")
print(weekly.to_dataframe())

# Create alert report
from episia.data import AlertEngine
from episia.api import EpiReport

engine = AlertEngine(ds)
alerts = engine.run(threshold=5, zscore_threshold=2.0)
summary = engine.alert_summary(alerts)

if summary['n_alerts'] > 0:
    report = EpiReport(
        title="Meningitis Alert Report2024",
        author="Epidemiological Service, MOH",
        institution="Ministry of Health - Burkina Faso",
    )
    
    report.add_metrics({
        "Total cases":      ds.total_cases,
        "Total deaths":     ds.total_deaths,
        "CFR":              f"{100*ds.total_deaths/ds.total_cases:.1f}%",
        "Alerts triggered": summary['n_alerts'],
        "Alert level":      summary['max_severity'],
    })
    
    report.add_text(
        f"Meningitis surveillance detected {summary['n_alerts']} alert weeks in 2024. "
        f"Review implementation of response protocols.",
        title="Summary",
    )
    
    # Save and export
    path = report.save_html("meningitis_alert_2024.html")
    print(f"Report saved: {path}")

# Push back to DHIS2 (optionalwrite cleaned/analyzed data)
# Note: Requires DHIS2 write permissions
cleaned_values = {
    "dataElement": "xyz789",  # Meningitissuspected (cleaned) UID
    "period": "202401",
    "orgUnit": "ImspD0yaksKo",
    "value": 45,
}
# client.post_data_value(cleaned_values)  # Uncomment with proper credentials
```

**Full DHIS2 Workflow:**

```python
from episia.dhis2 import DHIS2Client, DHIS2Adapter
from episia.models import SEIRModel
from episia.models.parameters import SEIRParameters
from episia import epi

# Connect to DHIS2
client = DHIS2Client(
    base_url="https://dhis2.example.com",
    username="admin",
    password="password"
)

# Fetch historical cases
historical_cases = client.get_data_values(
    data_element="uid_of_disease",
    period="202201:202412",
    org_units="region_uid",
)

# Create surveillance dataset
adapter = DHIS2Adapter()
ds = adapter.to_surveillance_dataset(
    historical_cases,
    date_col="period",
    cases_col="value",
)

print(f"Loaded {ds.total_cases} cases from {len(ds.dates)} reporting periods")

# Fit SEIR model to observed data
from episia.models import ModelCalibrator

calibrator = ModelCalibrator(
    model_class=SEIRModel,
    observed_data=ds.to_dataframe(),
    target_column="cases",
)

fitted_params = calibrator.fit(
    initial_params=SEIRParameters(N=1_500_000, beta=0.3, sigma=1/5.2, gamma=1/14),
    bounds={"beta": (0.1, 0.8), "gamma": (1/21, 1/7)},
)

print(f"Best fit: R0 = {fitted_params.r0:.2f}")

# Forecast
result = SEIRModel(fitted_params).run()
result.plot().show()

# Generate report for health ministry
report = epi.report(result, title="Meningitis Forecast 2025")
report.save_html("forecast_2025.html")

# (Optional) Push forecast to DHIS2 as target/projection
# for_write = adapter.from_model_result(result, data_element_uid="target_uid")
# client.post_data_values(for_write)
```

---

### `episia.api.reporting` – Report generation

```python
from episia.models import SEIRModel
from episia.models.parameters import SEIRParameters
from episia import EpiReport, report_from_model
from episia.viz import plot_epicurve
import webbrowser, os

# Auto-generate a full model report
params = SEIRParameters(
    N=22_100_000, I0=1, E0=10,
    beta=0.35, sigma=1/5.2, gamma=1/14,
    t_span=(0, 365),
)
model_result = SEIRModel(params).run()

report = report_from_model(
    model_result,
    title="SEIR Analysis - Burkina Faso 2024",
    author="Dr. F. Ariel Shadrac Ouedraogo",
    institution="Xcept-Health",
)
path = report.save_html("report.html")
webbrowser.open(f"file:///{os.path.abspath(path)}")

# Build a custom epidemiological bulletin
report = EpiReport(
    title="Weekly Epidemiological Bulletin - Week 12",
    author="Regional Health Authority",
    institution="Ministry of Health - Burkina Faso",
)

report.add_text(
    "This bulletin covers epidemiological events for the week of March 17-23, 2025.",
    title="Summary",
)

report.add_metrics({
    "Meningitis cases":   42,
    "Deaths":             3,
    "Case fatality rate": "7.1%",
    "Attack rate":        "8.4 / 100,000",
    "Alert districts":    4,
})

fig = plot_epicurve(
    times=model_result.t,
    values=model_result.compartments["I"],
    title="Epidemic curve",
    xlabel="Day",
    ylabel="Infectious",
)
report.add_figure(fig, title="Epidemic curve", caption="Weekly cases, Centre Region.")
report.add_divider()

# Export in multiple formats
report.save_html("bulletin_w12.html")
report.save_markdown("bulletin_w12.md")
report.save_json("bulletin_w12.json")
```

Report output is a self-contained HTML file with glassmorphism design, automatic dark/light mode based on system preference, and a copy-to-clipboard button.

---

## Project Structure

```
src/episia/
├ api/
│   ├ results.py          Unified result classes (EpiResult, ModelResult, ROCResult)
│   ├ unified.py          epi singletonconvenience entry point
│   └ reporting.py        EpiReport builder → HTML / Markdown / JSON
│
├ models/
│   ├ base.py             CompartmentalModel abstract class
│   ├ sir.py              SIRdS/dt dI/dt dR/dt
│   ├ seir.py             SEIRadds latent compartment E
│   ├ seird.py            SEIRDadds death compartment D
│   ├ parameters.py       SIRParameters, SEIRParameters, SEIRDParameters, ScenarioSet
│   ├ solver.py           solve_ivp wrapper, HIT, doubling time
│   ├ calibration.py      ModelCalibratorL-BFGS-B parameter fitting
│   ├ scenarios.py        ScenarioRunner, ScenarioResults
│   └ sensitivity.py      SensitivityAnalysisMonte Carlo
│
├ stats/
│   ├ contingency.py      Table2x2, risk_ratio, odds_ratio
│   ├ descriptive.py      proportion_ci, mean_ci, incidence_rate
│   ├ diagnostic.py       diagnostic_test_2x2, roc_analysis
│   ├ samplesize.py       sample_size_*, power_calculation
│   ├ stratified.py       Mantel-Haenszel, Breslow-Day
│   ├ regression.py       Logistic / Poisson regression
│   └ time_series.py      Epidemic curves, trend analysis
│
├ viz/
│   ├ plotters/           Plotly + Matplotlib backends, AnimationConfig
│   ├ themes/             scientific, minimal, dark, colorblind (.mplstyle)
│   ├ curves.py           plot_epicurve, plot_trend, plot_incidence, plot_doubling
│   ├ roc.py              plot_roc, plot_roc_compare, plot_precision_recall
│   ├ forest.py           plot_forest, plot_meta_forest
│   └ contingency_plot.py plot_contingency, plot_measures
│
├ dhis2/
│   ├ client.py           DHIS2Clientconnects to DHIS2 instances
│   ├ adapter.py          DHIS2Adaptertransforms to Episia data structures
│   └ constants.py        Standard DHIS2 data element UIDs
│
├ data/
│   ├ dataset.py          Datasetpandas wrapper with epi methods
│   ├ io.py               read_csv, read_excel, from_pandas
│   ├ surveillance.py     SurveillanceDataset, AlertEngine, endemic_channel
│   └ transformers.py     EpidemiologicalTransformer, DateTransformer
│
├ core/
│   ├ validator.py        Input validation
│   ├ calculator.py       Optimised calculators with caching
│   ├ exceptions.py       EpisiaError, ValidationError, DataError
│   ├ utilities.py        EpiLoaderterminal animation
│   └ constants.py        CI methods, statistical thresholds
│
├ simulation/             Post-MVPstochastic models, networks, spatial
├ compatibility/          Post-MVPOpenEpi, R epiR interop
│
├ __init__.py             Public API surface
└ __main__.py             python -m episia → terminal reference
```

---

## Test Coverage

```
1390 tests0 failed0 xfailed
Coverage: 80% (target: 85% at v0.2.0)

test_core.py                 165 tests
test_stats.py                133 tests
test_models.py               108 tests
test_samplesize_stratified.py 104 tests
test_remaining.py            129 tests
test_reporting.py            135 tests
test_data_viz_unified.py     122 tests
test_main.py                  44 tests
test_datatypes.py             50 tests
```

---

## API Stability

**v0.1.0a1 is an alpha release.** Breaking changes may occur until v1.0.0.

| Module | Status | Notes |
|--------|--------|-------|
| **episia.models** | Stable  | Core API frozen for v0.1+ |
| **episia.stats** | Stable  | All functions validated vs OpenEpi |
| **episia.api** | Stable  | Result objects, reporting API |
| **episia.data** | Stable  | Dataset, SurveillanceDataset |
| **episia.viz** | Experimental  | Plotly working; Matplotlib coverage improving |
| **episia.dhis2** | Experimental  | Core endpoints tested; some features pending |
| **episia.simulation** | Placeholder  | Post-MVPstochastic models coming v0.2 |
| **episia.compatibility** | Placeholder  | Post-MVPR/OpenEpi interop coming v0.2 |

Subscribe to [releases](https://github.com/Xcept-Health/episia/releases) for migration guides.

---

## Roadmap

| Version | Focus | Target | Status |
|---------|-------|--------|--------|
| **0.1.0** | Core models, stats, viz, DHIS2 adapter | March 2026 |  Complete |
| **0.1.1** | Bug fixes, docs | April 2026 | Planning |
| **0.2.0** | Stochastic models, expanded DHIS2 | Q2 2026 | Planned |
| **0.3.0** | Spatial epidemiology, Bayesian methods | Q3 2026 | Planned |
| **0.4.0** | Real-time forecasting, ensemble methods | Q4 2026 | Planned |
| **1.0.0** | API stable, production-ready | 2027 | Roadmap |

**Known Limitations (v0.1.0a1):**
- Simulation module (networks, spatial) is placeholder
- DHIS2 client covers POST/GET cases and basic metadata
- Browser plotter (36% coverage) is experimental; use Plotly or Matplotlib for production
- Documentation website launching at v0.2.0

---

## Citation

If you use Episia in your research, please cite it as:

**BibTeX:**
```bibtex
@software{ouedraogo2026episia,
  author = {Ouedraogo, Fildouindé Ariel Shadrac},
  title = {Episia: Open-source epidemiology and biostatistics for {P}ython},
  year = {2026},
  url = {https://github.com/Xcept-Health/episia},
  version = {0.1.0a1},
  organization = {Xcept-Health},
  address = {Ouagadougou, Burkina Faso}
}
```

**APA:**
```
Ouedraogo, F. A. S. (2026). Episia: Open-source epidemiology and biostatistics for Python (Version 0.1.0a1) [Computer software]. Xcept-Health. https://github.com/Xcept-Health/episia
```

**MLA:**
```
Ouedraogo, Fildouindé Ariel Shadrac. "Episia: Open-source epidemiology and biostatistics for Python." Version 0.1.0a1, Xcept-Health, 2026, https://github.com/Xcept-Health/episia.
```

---

## About

**Author:** Fildouindé Ariel Shadrac Ouedraogo  
**Organization:** [Xcept-Health](https://xcept-health.com), Ouagadougou, Burkina Faso  
**Affiliation:** MD Candidate, Université Joseph Ki-Zerbo, Department of Medicine  
**GitHub:** [@arielshadrac](https://github.com/arielshadrac)

**Validation:** Validated against OpenEpi reference implementation  
**Funding:** Independent research, supported by Xcept-Health initiative  
**Language:** English (code, documentation, tests)

Episia is an open-source health informatics project developed independently in Ouagadougou, 
Burkina Faso and supported by Xcept-Health. Built for epidemiological analysis in 
resource-limited African contexts.

---

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request.

```bash
git clone https://github.com/Xcept-Health/episia.git
cd episia
pip install -e ".[dev]"
pytest tests/ -v
```

**Code style:** `black` + `isort`. Type hints required for all public functions. Tests required for all new features (target: 80% coverage).

**Report bugs:** [GitHub Issues](https://github.com/Xcept-Health/episia/issues)  
**Discuss ideas:** [GitHub Discussions](https://github.com/Xcept-Health/episia/discussions)

---

## Support

- **Documentation:** [Full docs](https://docs.episia.io)
- **Examples:** [Examples directory](examples/)
- **Validation:** [OpenEpi comparison notebook](examples/episia_vs_openepi.ipynb)
- **Issues:** [GitHub Issues](https://github.com/Xcept-Health/episia/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Xcept-Health/episia/discussions)

---

## Scientific References

- Kermack, W.O. & McKendrick, A.G. (1927). *A Contribution to the Mathematical Theory of Epidemics.* Proc. Royal Society A, 115, 700-721.
- Anderson, R.M. & May, R.M. (1991). *Infectious Diseases of Humans.* Oxford University Press.
- OpenEpi. (2013). *Open Source Epidemiologic Statistics for Public Health.* [openepi.com](https://openepi.com)
- Dean, A.G. et al. (2013). *Epi Info.* CDC Atlanta.
- Wilson, E.B. (1927). *Probable Inference, the Law of Succession, and Statistical Inference.* JASA, 22(158), 209-212.
- Wong, B. (2011). *Points of view: Color blindness.* Nature Methods, 8, 441.
- Cori, A. et al. (2013). *A new framework and software to estimate time-varying reproduction numbers.* AJE, 178(9), 1505-1512.
- World Health Organization. (2014). *Control of epidemic meningococcal disease: WHO practical guidelines.*

---

## License

MIT Licensesee [LICENSE](LICENSE) for details.

Copyright © 2026 Xcept-Health

---

## FAQ

**Q: Why validate against OpenEpi?**  
A: OpenEpi is the gold standard in epidemiology. Full concordance ensures Episia results are trusted in field settings and peer-reviewed publications.

**Q: Can I use this in production?**  
A: Core modules (models, stats) are production-ready (80% coverage). See [API Stability](#api-stability) section. Simulation module is experimental.

**Q: How do I contribute?**  
A: Fork, create a feature branch, add tests, and submit a PR. See [Contributing](#contributing) section.

**Q: Is there a GUI?**  
A: Not yet. Episia is a Python library. Consider Jupyter notebooks or Streamlit for dashboards. See [examples/](examples/).

**Q: Does it work offline?**  
A: Yes. Episia has zero runtime network dependencies. DHIS2 integration requires connection only during data fetch.

**Q: What Python versions are supported?**  
A: Python 3.9, 3.10, 3.11, 3.12. See [pyproject.toml](pyproject.toml).

---

<div align="center">

Built with precision for African public health · [Xcept-Health](https://xcept-health.com) · Burkina Faso

![Status](https://img.shields.io/badge/Made%20with-Python%203.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-0.1.0a1-orange)

</div>
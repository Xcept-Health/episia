# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Episia is an open-source Python library for epidemiology and biostatistics: compartmental epidemic models (SIR/SEIR/SEIRD), OpenEpi-validated statistical measures, surveillance tooling, DHIS2 integration, visualization, and automated report generation. Targets resource-limited (francophone African) public health settings. Python 3.9+. Uses a `src/` layout (`src/episia/`).

## Commands

```bash
pip install -e ".[dev]"          # editable install with dev tools (pytest, black, isort, mypy, flake8)
pip install -e ".[full]"         # all optional runtime extras (kaleido, sklearn, seaborn, openpyxl, ...)

pytest tests/ -v                 # full suite (~1390 tests)
pytest tests/unit/test_stats.py -v               # one file
pytest tests/unit/test_stats.py::test_name -v    # one test
pytest tests/ -n auto            # parallel (pytest-xdist)
pytest tests/ --cov=episia       # coverage (pytest-cov)

black src/ tests/                # format
isort src/ tests/               # import order
mypy src/                       # type check
python -m episia                # CLI: prints terminal quick reference
```

There is no pytest config file or Makefile — invoke tools directly. Tests live in `tests/unit/`.

## Architecture

The codebase is organized around two central conventions. Internalize these before editing — most files participate in one or both.

### 1. Unified result objects (`api/results.py`)

Nearly every public function returns an `EpiResult` subclass rather than a bare value. `EpiResult` (ABC) guarantees `.to_dict()`, `.to_dataframe()`, and `.plot(backend=...)`. Subclasses include `AssociationResult` (risk/odds ratio), `ProportionResult`, `DiagnosticResult`, `ROCResult`, `ModelResult` (compartmental runs), `TimeSeriesResult`, `StratifiedResult`, `RegressionResult`, `SampleSizeResult`. These objects are rich, serializable, and printable (`__repr__` gives the human summary). When adding a new analysis function, return an existing result type or add a new `EpiResult` subclass — do not return raw tuples/dicts.

### 2. Compartmental model template (`models/base.py`)

`CompartmentalModel` (ABC) implements `run()` and `_build_result()` once; concrete models (`sir.py`, `seir.py`, `seird.py`) only implement the abstract hooks: `_derivatives(t, y)`, `_initial_state()`, `_compute_metrics(...)`, and the compartment-name property. Integration goes through `models/solver.py` (a `scipy.solve_ivp` wrapper that also computes R0, herd-immunity threshold, doubling time). Parameters are dataclasses in `models/parameters.py` (`SIRParameters`, `SEIRParameters`, `SEIRDParameters`, `ScenarioSet`). To add a model, subclass `CompartmentalModel` and add a matching parameters dataclass — `run()`/result-building come for free.

Higher-level model drivers compose these: `ModelCalibrator` (`calibration.py`, L-BFGS-B fitting to observed data), `SensitivityAnalysis` (`sensitivity.py`, Monte Carlo over parameter distributions), `ScenarioRunner` (`scenarios.py`, multi-scenario envelope comparison).

### Module map

- `api/unified.py` — the `epi` singleton (`EpisiaAPI`), a thin convenience facade re-exporting models/stats/viz/reporting. The README and most user code enter through `from episia import epi`.
- `api/reporting.py` — `EpiReport` builder → self-contained HTML / Markdown / JSON. `report_from_model`, `report_from_result`.
- `stats/` — `contingency.py` (`Table2x2`, risk/odds ratio), `descriptive.py`, `diagnostic.py`, `samplesize.py`, `stratified.py` (Mantel-Haenszel), `regression.py` (logistic/Poisson IRLS), `time_series.py`. All validated against OpenEpi.
- `viz/` — every plot function takes `backend="plotly"` (default, interactive) or `backend="matplotlib"` (300 DPI, publication). Backends live in `viz/plotters/`; themes (`scientific`, `minimal`, `dark`, `colorblind`) are `.mplstyle` files in `viz/themes/` (packaged via `package_data`).
- `data/` — `SurveillanceDataset` + `AlertEngine` (threshold / z-score / endemic-channel alerting), `dataset.py`, `io.py`, `transformers.py`.
- `dhis2/` — `DHIS2Client` (REST against a DHIS2 instance) + `DHIS2Adapter` (converts DHIS2 payloads to `SurveillanceDataset`). The only module that touches the network, and only during explicit fetch; everything else is offline.
- `core/` — `validator.py`, `calculator.py` (cached calculators), `exceptions.py` (`EpisiaError`, `ValidationError`, `DataError`), `utilities.py` (`EpiLoader` terminal animation), `constants.py` (CI methods, thresholds).
- `simulation/`, `compatibility/` — placeholders for post-v0.2 work (stochastic/spatial models, R/OpenEpi interop). Not yet implemented.

### Conventions

- Public API surface is curated in `src/episia/__init__.py` (`__all__`); `__version__` is defined there and read by `setup.py` via regex (not import). Bump it there for releases.
- Type hints required on public functions; tests required for new features (coverage target 80%).
- Runtime must stay offline except `dhis2`. Don't add network calls elsewhere.
- `setup.py` lists `Cython` as a build requirement, but there are currently no `.pyx` sources — the package is pure Python.

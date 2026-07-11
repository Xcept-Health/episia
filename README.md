<div align="center">

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
- Jupyter notebook support

---

## Validation

Episia is systematically validated against [OpenEpi](https://openepi.com), the reference in epidemiology. All results from core functions (risk ratio, odds ratio, confidence intervals, χ² tests, etc.) have been compared and agree with OpenEpi on standard datasets.

**[Check out the full validation notebook](https://github.com/Xcept-Health/episia/blob/main/exemples/episia_vs_openepi.ipynb)**

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

| Extra                           | What it adds                                         |
| ------------------------------- | ---------------------------------------------------- |
| `pip install episia[full]`    | ipywidgets, kaleido, scikit-learn, seaborn, openpyxl |
| `pip install episia[jupyter]` | Jupyter + interactive widgets                        |
| `pip install episia[export]`  | PNG/SVG/PDF export via kaleido                       |
| `pip install episia[dev]`     | pytest, black, mypy, pre-commit                      |

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

Episia is organized into six modules. Full documentation with code examples for each lives on [ReadTheDocs](https://episia.readthedocs.io/en/latest/); the tables below are a quick-reference summary.

### `episia.models` – Compartmental epidemic models

| Class / Function        | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `SIRModel`            | Classic SIR  dS/dt, dI/dt, dR/dt                 |
| `SEIRModel`           | SEIR with latent (exposed) compartment           |
| `SEIRDModel`          | SEIRD with disease-induced mortality             |
| `ModelCalibrator`     | Fit model parameters to observed data (L-BFGS-B) |
| `SensitivityAnalysis` | Monte Carlo parameter uncertainty analysis       |
| `ScenarioRunner`      | Multi-scenario comparison with envelope plots    |

→ [Models documentation](https://episia.readthedocs.io/en/latest/models/index.html) · [Interactive SEIR example](exemples/seir_interactive_with_matplotlib.py)

### `episia.stats` – Biostatistics & epidemiological measures

| Function                                            | Returns                 | Description                                                             |
| --------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------- |
| `risk_ratio(a, b, c, d)`                          | `AssociationResult`   | Risk ratio with CI                                                      |
| `odds_ratio(a, b, c, d)`                          | `AssociationResult`   | Odds ratio with CI                                                      |
| `proportion_ci(k, n)`                             | `ProportionResult`    | Proportion CI — Wilson, Wald, Jeffreys, Clopper-Pearson, Agresti-Coull |
| `prevalence(cases, population)`                   | `ProportionResult`    | Point prevalence with CI                                                |
| `cumulative_incidence(cases, population_at_risk)` | `ProportionResult`    | Cumulative incidence (attack rate / risk) with CI                       |
| `incidence_rate(cases, person_time)`              | `IncidenceRateResult` | Person-time incidence rate — Byar + exact Poisson CI                   |
| `mean_ci(data)`                                   | `MeanResult`          | Mean with t / normal CI                                                 |
| `diagnostic_test_2x2(tp, fp, fn, tn)`             | `DiagnosticResult`    | Sensitivity, specificity, PPV, NPV, LR+/-                               |
| `roc_analysis(y_true, y_score)`                   | `ROCResult`           | Full ROC curve, AUC, optimal threshold (Youden)                         |
| `sample_size_risk_ratio(...)`                     | `SampleSizeResult`    | Sample size for cohort study                                            |
| `sample_size_single_proportion(...)`              | `SampleSizeResult`    | Sample size for prevalence survey                                       |
| `mantel_haenszel_or(strata)`                      | `StratifiedResult`    | Pooled OR/RR with Cochran Q, I²                                        |
| `logistic_regression(X, y)`                       | `RegressionResult`    | Logistic regression, IRLS                                               |
| `poisson_regression(X, y)`                        | `RegressionResult`    | Poisson regression with offset support                                  |

All measures are validated against OpenEpi — see the [validation notebook](exemples/episia_vs_openepi.ipynb).

→ [Stats documentation](https://episia.readthedocs.io/en/latest/stats/index.html)

### `episia.viz` – Visualization

Epidemic curves, endemic channels, ROC curves, forest plots, and model trajectories, with dual Plotly (interactive) and Matplotlib (publication-quality, static export) backends, plus configurable themes.

→ [Viz documentation](https://episia.readthedocs.io/en/latest/viz/index.html)

### `episia.data` – Surveillance data

`SurveillanceDataset` wraps raw CSV/DataFrame surveillance data with epidemiology-aware helpers: attack rate per 100,000, weekly/monthly/yearly aggregation, endemic channel (historical percentile envelope), and threshold/z-score/endemic-channel alert detection.

→ [Data documentation](https://episia.readthedocs.io/en/latest/data/index.html)

### `episia.dhis2` – DHIS2 Integration

Native client for the DHIS2 API: connect, build period strings, fetch analytics data directly as a `SurveillanceDataset`, and check reporting completeness — useful for detecting silent reporting gaps, common in DHIS2 deployments across sub-Saharan Africa.

→ [DHIS2 documentation](https://episia.readthedocs.io/en/latest/dhis2/index.html) · [DHIS2 quickstart walkthrough](https://episia.readthedocs.io/en/latest/quickstart.html#dhis2-integration)

### `episia.api.reporting` – Report generation

Turns any model or stats result into a self-contained HTML/Markdown/JSON report — glassmorphism design, automatic dark/light mode, no external dependencies to view. Supports custom bulletins combining multiple figures, tables, and text sections.

→ [Reporting documentation](https://episia.readthedocs.io/en/latest/modules/api/reporting.html) · [Quick report example](exemples/Quick_report.py)

---

## API Stability

**v0.1.3 is a stable release of the core API.** Breaking changes remain possible until v1.0.0, and will be documented in the changelog.

| Module                         | Status       | Notes                                         |
| ------------------------------ | ------------ | --------------------------------------------- |
| **episia.models**        | Stable       | Core API frozen for v0.1+                     |
| **episia.stats**         | Stable       | All functions validated vs OpenEpi            |
| **episia.api**           | Stable       | Result objects, reporting API                 |
| **episia.data**          | Stable       | Dataset, SurveillanceDataset                  |
| **episia.viz**           | Experimental | Plotly working; Matplotlib coverage improving |
| **episia.dhis2**         | Experimental | Core endpoints tested; some features pending  |
| **episia.simulation**    | Placeholder  | Post-MVPstochastic models coming v0.2         |
| **episia.compatibility** | Placeholder  | Post-MVPR/OpenEpi interop coming v0.2         |

Subscribe to [releases](https://github.com/Xcept-Health/episia/releases) for migration guides.

---

## Roadmap

| Version         | Focus                                   | Target     | Status   |
| --------------- | --------------------------------------- | ---------- | -------- |
| **0.1.0** | Core models, stats, viz, DHIS2 adapter  | March 2026 | Complete |
| **0.1.1** | Bug fixes, docs                         | April 2026 | complete |
| **0.2.0** | Stochastic models, expanded DHIS2       | Q2 2026    | Planned  |
| **0.3.0** | Spatial epidemiology, Bayesian methods  | Q3 2026    | Planned  |
| **0.4.0** | Real-time forecasting, ensemble methods | Q4 2026    | Planned  |
| **1.0.0** | API stable, production-ready            | 2027       | Roadmap  |

**Known Limitations (v0.1.3):**

- Simulation module (networks, spatial) is placeholder
- DHIS2 client covers POST/GET cases and basic metadata
- Browser plotter (36% coverage) is experimental; use Plotly or Matplotlib for production
- Documentation website launching at v0.2.0

---

## Citation

A preprint describing Episia is available on medRxiv:

> Ouedraogo FAS. *Episia: An Open-Source Python Library for Epidemiological Surveillance, Modeling, and Biostatistics in Resource-Limited Settings.* medRxiv 2026. https://doi.org/10.64898/2026.04.17.26350337

If you use Episia in your research, please cite it as:

**BibTeX:**

```bibtex
@article{ouedraogo2026episia_preprint,
  author  = {Ouedraogo, Fildouind{\'e} Ariel Shadrac},
  title   = {Episia: An Open-Source Python Library for Epidemiological
             Surveillance, Modeling, and Biostatistics in Resource-Limited Settings},
  journal = {medRxiv},
  year    = {2026},
  doi     = {10.64898/2026.04.17.26350337},
  url     = {https://doi.org/10.64898/2026.04.17.26350337},
  note    = {Preprint}
}
```

```bibtex
@software{ouedraogo2026episia,
  author = {Ouedraogo, Fildouindé Ariel Shadrac},
  title = {Episia: Open-source epidemiology and biostatistics for {P}ython},
  year = {2026},
  doi = {10.5281/zenodo.19429374},
  url = {https://doi.org/10.5281/zenodo.19429374},
  note = {Source code: https://github.com/Xcept-Health/episia},
  version = {0.1.3},
  organization = {Xcept-Health},
  address = {Ouagadougou, Burkina Faso}
}
```

**Vancouver:**

```
Ouedraogo FAS. Episia: Open-source epidemiology and biostatistics for Python [Computer software]. Version 0.1.3. Ouagadougou: Xcept-Health; 2026. Available from: https://doi.org/10.5281/zenodo.19429374
```

**APA:**

```
Ouedraogo, F. A. S. (2026). Episia: Open-source epidemiology and biostatistics for Python (Version 0.1.3) [Computer software]. Xcept-Health. https://doi.org/10.5281/zenodo.19429374
```

**MLA:**

```
Ouedraogo, Fildouindé Ariel Shadrac. "Episia: Open-source epidemiology and biostatistics for Python." Version 0.1.3, Xcept-Health, 2026, https://doi.org/10.5281/zenodo.19429374.
```

---

## About

**Author:** Fildouindé Ariel Shadrac Ouedraogo
**ORCID:** [0009-0003-3419-5985](https://orcid.org/0009-0003-3419-5985)
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

**Code style:** `black` + `isort`. Type hints required for all public functions. Tests required for all new features (target: 85% coverage).

**Report bugs:** [GitHub Issues](https://github.com/Xcept-Health/episia/issues)
**Discuss ideas:** [GitHub Discussions](https://github.com/Xcept-Health/episia/discussions)

---

## Support

- **Documentation:** [Full docs](https://docs.episia.io)
- **Examples:** [Examples directory](exemples/)
- **Validation:** [OpenEpi comparison notebook](exemples/episia_vs_openepi.ipynb)
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
A: Core modules (models, stats) are production-ready (84% coverage). See [API Stability](#api-stability) section. Simulation module is experimental.

**Q: How do I contribute?**
A: Fork, create a feature branch, add tests, and submit a PR. See [Contributing](#contributing) section.

**Q: Is there a GUI?**
A: Not yet. Episia is a Python library. Consider Jupyter notebooks or Streamlit for dashboards. See [exemples/](exemples/).

**Q: Does it work offline?**
A: Yes. Episia has zero runtime network dependencies. DHIS2 integration requires connection only during data fetch.

**Q: What Python versions are supported?**
A: Python 3.9, 3.10, 3.11, 3.12. See [pyproject.toml](pyproject.toml).

---

<div align="center">

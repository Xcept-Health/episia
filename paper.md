---
title: 'Episia: An Open-Source Python Library for Epidemiology and Biostatistics in Resource-Limited Settings'

tags:
  - Python
  - epidemiology
  - biostatistics
  - compartmental models
  - public health
  - Africa
  - DHIS2
  - surveillance

authors:
  - name: Fidlouindé Ariel Shadrac OUEDRAOGO
    orcid: 0009-0003-3419-5985
    affiliation: "1, 2"
affiliations:
  - name: Independent Researcher, Burkina Faso
    index: 1
  - name: xcept-health, Burkina Faso
    index: 2

date: 2026-03-19

bibliography: paper.bib
---

# Summary

Episia is an open-source Python library designed for public health researchers, field epidemiologists, and biostatisticians working in resource-limited settings. It provides a unified and validated toolkit for
epidemiology and biostatistics. It incorporates compartmental epidemic models (SIR, SEIR, SEIRD), classical biostatistical analyses (risk ratio, odds ratio, diagnostic test evaluation, ROC analysis, sample size calculation), surveillance data processing, automated report generation, and native integration with the DHIS2 health information platform used throughout sub-Saharan Africa.

Episia is the first Python library to bring these features together within a single, consistent API, validated against OpenEpi [@openepi], the gold standard implementation in field epidemiology. All essential statistical functions have been compared to OpenEpi on standard datasets, with agreement achieved across 45 independent test cases. Requiring no cloud dependencies, it is designed to operate 100% offline and to function in district hospitals, field missions, and low-connectivity environments characteristic of African healthcare systems.


# Statement of Need

Epidemiological analysis in resource-limited settings poses specific challenges that are rarely, if ever, addressed by existing software. Burkina Faso and its neighboring countries in the Sahel face recurring epidemic threats bacterial meningitis, cholera, malaria, and dengue fever which require rapid, validated analytical processes capable of functioning without reliable internet access. Burkina Faso’s national health information system, like those of more than 40 African countries, runs on DHIS2 [@dhis2], but no existing Python library offers direct integration with this platform along with comprehensive biostatistical and modeling capabilities

The available tools force analysts to adopt fragmented workflows: epiR [@epir], for example, covers epidemiological statistics but requires R and does not offer epidemic modeling; EpiEstim [@cori2013] is limited to R(t) estimation; compartmental model libraries such as EpiPy provide basic SIR/SEIR models, but do not incorporate biostatistics or surveillance. Statsmodels [@seabold2010], meanwhile, offers general regression but is not suited to
epidemiological use cases. None of these tools generates automated HTML reports, none integrates with DHIS2, and none is designed for the public health context in Africa.

Episia fills this gap by enabling the management of the entire epidemiological process from raw DHIS2 surveillance data through epidemiological models and biostatistical analyses to HTML reports ready for publication all within a single Python module, accessible to analysts who may have limited computing resources and no internet connection.


# State of the Field

Several open-source tools cover certain stages of the epidemiological process. These include, among others: 
epiR [@epir], the most comprehensive epidemiological statistics package for R; it allows, in particular, the analysis of 2×2 tables, the application of Mantel-Haenszel methods, and the calculation of sample size, but it requires R and does not support epidemic modeling or the DHIS2 interface.
EpiEstim [@cori2013], which provides a principle-based estimate of R(t), but is a one-time-use tool.
EpiModel[@jenness2018], which supports network-based stochastic models in R.
PyMC [@salvatier2016] and Stan [@carpenter2017], which enable Bayesian inference on epidemics, but require in-depth statistical expertise and are not designed for use in the field.
OpenEpi [@openepi], which is an online calculator widely used in epidemiology training but cannot be integrated into program workflows.

Other examples include Python-based compartmental model libraries (EpiPy, PyEpiLib), which implement basic models based on ordinary differential equations (ODEs) but do not support calibration, sensitivity analysis using the Monte Carlo method, or multimodal results. None of the aforementioned tools, although effective and widely used, support surveillance alert detection, integration with DHIS2, or automated report generation.

Episia thus positions itself as a complement to this ecosystem, with a focus on Africa and a preference for Python.
To this end, it offers data import from DHIS2, calculates validated biological statistics, runs
compartmental models with uncertainty quantification, and generates standalone reports—all from a single installation and without requiring network access during execution.

# Software Design

## Architecture

Episia is structured as a modular Python package with eight functional subsystems:

- **`episia.stats`** for biostatistical analysis: contingency tables, diagnostic tests, ROC analysis, logistic and Poisson regression, stratified analyses, sample size calculations, and time series methods. All functions return serializable result objects containing point estimates, confidence intervals, and p-values.

- **`episia.models`** provides compartmental epidemiological models (SIR, SEIR, SEIRD) solved using `scipy.integrate.solve_ivp`, supporting model calibration (L-BFGS-B), comparison of multiple scenarios, and sensitivity analysis via the Monte Carlo method with uniform, normal, and triangular parameter distributions.

- **`episia.data`** for data ingestion and transformation: importing DHIS2-compatible CSV files, memory-optimized type inference, outlier detection, and feature engineering.

- **`episia.dhis2`**: the native DHIS2 client, supporting authentication via Basic Authentication and Personal Access Tokens, requests via the analytics API, as well as automatic period analysis (ISO week, monthly, quarterly, annual) via `DHIS2Client` and `DHIS2Adapter`.

- **`episia.data.surveillance`**, which provides `SurveillanceDataset` and `AlertEngine` for structured epidemiological surveillance: alert detection based on thresholds, z-scores, and endemic channels.

- **`episia.viz`**, which stands out for its dual-engine visualization (Plotly for interactive results, Matplotlib for publication-quality plots) and offers four themes (scientific, minimalist, dark, and colorblind-friendly).

- **`episia.api`**: the unified high-level API accessible via the `epi` namespace, and `EpiReport` for the automated generation of standalone HTML reports.

- **`episia.core`**, which provides validation, an exception hierarchy, constants, and `EpiLoader`, a progress animation for the terminal that switches to silent mode in non-TTY environments.

## Validation

Each major statistical function in the episia.stats module has been systematically validated by comparison with OpenEpi [@openepi]. A dedicated test notebook faithfully reproduces OpenEpi’s 14 calculation modules. All 45 checks performed were successfully validated, with systematic numerical agreement to at least three decimal places.
For the sake of transparency and to ensure reproducibility, the complete validation notebook is available in the repository at:
examples/episia_vs_openepi.ipynb.

## Testing

La bibliothèque comprend 1 390 tests automatisés assurant une couverture de code de 80 %, mis en œuvre à l'aide de pytest. Les tests couvrent l'ensemble des modules, y compris des tests basés sur des simulateurs pour le client DHIS2, qui s'exécutent sans serveur en production. La suite de tests fonctionne sous Python 3.9–3.12 et est exécutée à chaque commit via GitHub Actions.

## Example Usage

```python
from episia import epi

# SEIR epidemic model Burkina Faso, bacterial meningitis
result = epi.seir(N=22_100_000, I0=10, E0=50,
                  beta=0.35, sigma=1/5.2, gamma=1/14).run()
print(result)
# SEIR Model  R0: 4.90  Peak: 331,751 at t=84.5  Final size: 99.2%

# Vaccine efficacy from cohort study (validated against OpenEpi)
rr = epi.risk_ratio(a=12, b=2988, c=87, d=2913)
ve = (1 - rr.estimate) * 100
print(f"Vaccine Efficacy: {ve:.1f}%  [{(1-rr.ci_upper)*100:.1f}%–{(1-rr.ci_lower)*100:.1f}%]")
# Vaccine Efficacy: 76.7%  [60.3%–86.3%]

# DHIS2 surveillance data
from episia.dhis2 import DHIS2Client
from episia.data.surveillance import AlertEngine
client = DHIS2Client(url="https://dhis2.sante.gov.bf",
                     username="admin", password="***")
ds = client.to_dataset(data_element="meningite_cases",
                       period="LAST_52_WEEKS", org_unit="LEVEL-3")
alerts = AlertEngine(ds).run(threshold=15, zscore_threshold=2.0)

# Automated HTML report
report = epi.report(result, title="SEIR Burkina Faso 2024")
report.save_html("rapport.html")
```


# Research Impact Statement

Episia a été développé chez Xcept-Health pour répondre à des besoins analytiques concrets rencontrés dans la pratique de la santé publique au Burkina Faso. Ses principales applications en matière de recherche comprennent :

**Outbreak Response.** The `SurveillanceDataset` and `AlertEngine` components implement the WHO’s “meningitis belt” detection algorithm [@who2014], enabling the automated identification of epidemic weeks based on weekly case reports from DHIS2. The SEIR and SEIRD models with uncertainty quantification enable rapid projection of epidemic trajectories and intervention scenarios.

**Vaccine programme evaluation.** Validated biostatistical methods (risk ratio, Mantel-Haenszel stratified odds ratio, logistic regression) enable the evaluation of post-campaign efficacy of vaccines such as MenAfriVac [@laforce2009], the meningococcal conjugate vaccine deployed in the Sahel region since 2010.

**Diagnostic test assessment.** The `diagnostic_test_2x2`, `roc_analysis`, and `predictive_values_from_sens_spec` functions support evaluation of point-of-care diagnostics (malaria RDTs, COVID-19 antigen tests) at variable field prevalences, supporting district-level procurement decisions.

**Training and capacity building.** Episia's unified API and included demo notebook (`examples/episia_demo.ipynb`) are designed for use in epidemiology training programmes at African schools of public health providing validated calculations and interactive visualizations without proprietary software requirements.

The library is published on PyPI (`pip install episia`) and maintained on [github.com/Xcept-Health/episia](https://github.com/Xcept-Health/episia) under the MIT license. The documentation and validation notebook are available at [xcept-health.github.io/episia](https://xcept-health.github.io/episia).


# AI Usage Disclosure

The author used Claude (Anthropic) as an AI coding assistant during development of
Episia. AI assistance was used for: generating boilerplate test code, debugging
specific numerical edge cases, and drafting docstrings. All architectural decisions,
statistical algorithm implementations, validation methodology, and domain-specific
design choices were made by the author. The core statistical implementations were
independently validated against OpenEpi reference outputs.


# Acknowledgements

The author thanks the Xcept-Health team for support during development, and the OpenEpi development team for providing a freely accessible reference implementation of epidemiological calculations that enabled systematic validation of Episia.
Development was conducted in Ouagadougou, Burkina Faso.


# References
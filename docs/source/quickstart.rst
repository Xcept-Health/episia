Quick Start
===========

This page walks through the four core things Episia is used for: running an
epidemic model, computing biostatistical measures, pulling surveillance data
from DHIS2, and generating a shareable report. Each section shows a minimal,
runnable snippet and explains what it produces. For the full function and
class reference, see :doc:`api_reference`.

Epidemic Model
--------------

Run a compartmental SEIR model to project how an outbreak spreads over time,
then visualize the resulting epidemic curve.

.. code-block:: python

    from episia import epi

    # Run SEIR model
    model = epi.seir(
        N=1_000_000,
        I0=10,
        E0=50,
        beta=0.35,
        sigma=1/5.2,
        gamma=1/14
    )
    result = model.run()
    print(result)

    # Plot results
    result.plot().show()

``result`` gives you the full trajectory (susceptible, exposed, infected,
recovered compartments over time) plus summary metrics such as R0, peak
infected count, and epidemic duration. See :doc:`models/index` for the SIR,
SEIR, and SEIRD model classes, and
`seir_interactive_with_matplotlib.py <https://github.com/Xcept-Health/episia/blob/main/exemples/seir_interactive_with_matplotlib.py>`_
for an interactive version with sliders to explore parameters live.

Biostatistics
-------------

Compute the classical epidemiological measures used to quantify association
and diagnostic performance, each systematically validated against OpenEpi
(see the `validation notebook <https://github.com/Xcept-Health/episia/blob/main/exemples/episia_vs_openepi.ipynb>`_).

.. code-block:: python

    from episia import epi

    # Calculate risk ratio
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)
    # Output: Risk Ratio: 2.667 (1.514-4.696)

    # Confidence interval for proportion
    prop = epi.proportion_ci(k=45, n=100)
    print(prop)
    # Output: Proportion: 0.4500 (0.354-0.549)

    # Diagnostic test evaluation
    diag = epi.diagnostic_test_2x2(tp=80, fp=20, fn=10, tn=90)
    print(f"Sensitivity: {diag.sensitivity:.3f}")
    print(f"Specificity: {diag.specificity:.3f}")

``risk_ratio`` and ``proportion_ci`` return result objects with point
estimates and confidence intervals, ready to print or feed into a report.
``diagnostic_test_2x2`` evaluates a 2x2 test-vs-reference table (sensitivity,
specificity, predictive values, likelihood ratios). See :doc:`stats/index`
for the full list of association measures, sample size calculators, and
regression tools.

DHIS2 Integration
------------------

Pull surveillance data directly from a DHIS2 instance into an
analysis-ready :class:`~episia.data.surveillance.SurveillanceDataset`, without
manual CSV exports.

.. code-block:: python

    from episia.dhis2 import DHIS2Client

    # Connect to DHIS2 demo instance
    client = DHIS2Client(
        url      = "https://play.dhis2.org/40.2.2",
        username = "admin",
        password = "district",
    )

    # Fetch surveillance data
    ds = client.to_dataset(
        data_element = "FTRrcoaog83",  # Malaria cases
        period       = "LAST_52_WEEKS",
        org_unit     = "ImspTQPwCqd",   # Sierra Leone
    )

    print(f"Loaded {ds.total_cases} cases")
    print(f"Date range: {ds.date_range}")

    # Generate epidemic curve
    ds.to_timeseries_result().plot().show()

This connects to a public DHIS2 demo server so the snippet runs as-is; swap
in your own instance's URL and credentials for real surveillance data. See
:doc:`dhis2/index` for authentication options, period-string helpers, and
reporting-completeness checks (useful for detecting silent gaps in
sub-Saharan African DHIS2 deployments).

Reporting
---------

Turn a model result into a shareable, self-contained report (HTML,
Markdown, or JSON) with no external dependencies at read time.

.. code-block:: python

    from episia import epi

    # Generate report from model result
    report = epi.report(
        result,
        title="SEIR Model - Burkina Faso 2024",
        author="Dr. Ouedraogo"
    )

    # Export in multiple formats
    report.save_html("report.html")
    report.save_markdown("report.md")
    report.save_json("report.json")

``report.save_html`` produces a standalone HTML file (charts embedded, no
internet connection needed to view it) suitable for sharing with ministries
of health or field teams. See
`Quick_report.py <https://github.com/Xcept-Health/episia/blob/main/exemples/Quick_report.py>`_
for a script that runs a model, prints a risk ratio, and opens the generated
report in your browser in one go.

Next Steps
----------

- **Full API reference**: :doc:`api_reference` for every public function, class, and module.
- **Validation against OpenEpi**: `episia_vs_openepi.ipynb <https://github.com/Xcept-Health/episia/blob/main/exemples/episia_vs_openepi.ipynb>`_ compares Episia's statistical output against the reference tool.
- **Interactive dashboard**: `episia_streamlit.py <https://github.com/Xcept-Health/episia/blob/main/exemples/streamlit/episia_streamlit.py>`_, a Streamlit app covering models, biostatistics, and DHIS2 in a single UI.
- **More examples**: the `exemples/ directory <https://github.com/Xcept-Health/episia/tree/main/exemples>`_ for additional scripts.
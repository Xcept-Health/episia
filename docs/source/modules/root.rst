Episia Package
==============

.. automodule:: episia
   :members:
   :undoc-members:
   :show-inheritance:

Package Overview
----------------

The ``episia`` package provides a comprehensive toolbox for epidemiological analysis.
The recommended entry point is the unified ``epi`` interface:

.. code-block:: python

    from episia import epi

    # Unified API
    model = epi.seir(N=1_000_000, I0=10, E0=50, beta=0.35, sigma=1/5.2, gamma=1/14)
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    report = epi.report(result)

For advanced usage, individual modules can be imported directly.

Version Information
-------------------

.. data:: __version__
   :type: str
   :value: "0.1.0a1"

   Current version of Episia.

.. data:: __author__
   :type: str
   :value: "Fidlouindé Ariel Shadrac Ouedraogo"

   Package author.

.. data:: __email__
   :type: str
   :value: "arielshadrac@gmail.com"

   Author's email address.

.. data:: __organization__
   :type: str
   :value: "Xcept-Health"

   Organization name.

.. data:: __license__
   :type: str
   :value: "MIT"

   License type.

Lazy Loading
------------

Episia uses lazy loading to improve startup performance. Heavy modules
(``scipy``, ``sklearn``, ``plotly``, ``matplotlib``) are only imported when
first used. This means:

- ``from episia import epi`` is fast
- ``from episia import risk_ratio`` triggers the import of required dependencies

The lazy loading is implemented via PEP 562 (``__getattr__``).

Plotly Renderer Configuration
------------------------------

Episia automatically configures the Plotly renderer based on the environment:

- In **Jupyter notebooks**: Renderer is left unchanged (inline display works normally)
- In **scripts/terminals**: Renderer is set to ``"browser"`` to open figures in your web browser

This prevents raw JSON from being dumped in the terminal when calling ``fig.show()``.

Unified Interface
-----------------

.. autodata:: episia.epi
   :annotation: = EpisiaAPI()

   The main entry point for Episia functionality. Provides a unified interface
   to all modules through a single object.

.. autoclass:: episia.api.unified.EpisiaAPI
   :noindex:

Reporting
---------

.. autoclass:: episia.api.reporting.EpiReport
   :noindex:

.. autofunction:: episia.api.reporting.report_from_result
   :noindex:

.. autofunction:: episia.api.reporting.report_from_model
   :noindex:

Surveillance Data
-----------------

.. autoclass:: episia.data.surveillance.SurveillanceDataset
   :noindex:

.. autoclass:: episia.data.surveillance.AlertEngine
   :noindex:

Available Lazy Imports
----------------------

The following names are lazily loaded from their respective modules:

**Statistics:**
- ``risk_ratio``
- ``odds_ratio``
- ``proportion_ci``
- ``mean_ci``
- ``diagnostic_test_2x2``
- ``roc_analysis``
- ``sample_size_risk_ratio``
- ``sample_size_single_proportion``

**Visualization:**
- ``set_theme``
- ``get_available_themes``
- ``plot_epicurve``
- ``plot_roc``
- ``plot_forest``

Examples
--------

Basic usage with unified interface::

    from episia import epi

    # SEIR model
    model = epi.seir(
        N=1_000_000,
        I0=10,
        E0=50,
        beta=0.35,
        sigma=1/5.2,
        gamma=1/14
    )
    result = model.run()
    result.plot().show()

    # Risk ratio
    rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
    print(rr)  # Risk Ratio: 2.667 (1.514-4.696)

    # Generate report
    report = epi.report(result, title="SEIR Analysis")
    report.save_html("report.html")

Direct imports for advanced usage::

    from episia.models import SEIRModel, SensitivityAnalysis
    from episia.stats import roc_analysis, sample_size_risk_ratio
    from episia.viz import plot_epicurve, set_theme
    from episia.data import SurveillanceDataset

    # Set theme globally
    set_theme("dark")

    # Load surveillance data
    ds = SurveillanceDataset.from_csv("cases.csv")

    # ROC analysis
    roc_result = roc_analysis(y_true, y_scores)

Version check::

    import episia
    print(f"Episia version: {episia.__version__}")
Command-Line Interface
======================

.. automodule:: episia.__main__
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

Episia provides a command-line interface that displays a quick reference
guide, showing available modules and their key functions. This is useful
for getting started or reminding yourself of the API without leaving the
terminal.

Usage
-----

.. code-block:: bash

    python -m episia

Or if Episia is installed:

.. code-block:: bash

    episia

Output
------

When run, the command displays:

- A gradient-colored logo
- Version information
- Python version
- Module catalog with key functions for:
  - ``episia.models``: Compartmental epidemic models
  - ``episia.stats``: Biostatistics & epidemiological measures
  - ``episia.viz``: Visualization (Plotly & Matplotlib)
  - ``episia.data``: Surveillance data management
  - ``episia.api``: Reporting & unified interface
- A quick start code example
- GitHub repository link

Color Support
-------------

The CLI automatically detects terminal color support:

- On **Windows 10+** with VT100 emulation enabled: Full ANSI colors
- On **macOS/Linux** with TTY: Full ANSI colors
- On **other terminals** or when output is redirected: Plain text fallback

The gradient logo uses TrueColor (24-bit) ANSI escape sequences when supported.

Example Output
--------------

.. code-block:: text

 ███████╗██████╗ ██╗███████╗██╗ █████╗
 ██╔════╝██╔══██╗██║██╔════╝██║██╔══██╗
 █████╗  ██████╔╝██║███████╗██║███████║
 ██╔══╝  ██╔═══╝ ██║╚════██║██║██╔══██║
 ███████╗██║     ██║███████║██║██║  ██║
 ╚══════╝╚═╝     ╚═╝╚══════╝╚═╝╚═╝  ╚═╝

    Open-source epidemiology & biostatistics for Python
    v0.1.0a1 · Python 3.9.7 · Xcept-Health · MIT

    ────────────────────────────────────────────────────

    episia.models
        Compartmental epidemic models
        SIRModel(params).run()          → ModelResult
        SEIRModel(params).run()         → ModelResult
        SEIRDModel(params).run()        → ModelResult
        ModelCalibrator(...).fit()      → CalibrationResult
        SensitivityAnalysis(...).run()  → SensitivityResult
        ScenarioRunner(Model).run()     → ScenarioResults

    ...

    Quick start
        from episia import epi

        # Run a SEIR model
        model  = epi.seir(N=1_000_000, I0=10, E0=50,
                          beta=0.35, sigma=1/5.2, gamma=1/14)
        result = model.run()
        print(result)
        result.plot().show()

        # Compute a risk ratio
        rr = epi.risk_ratio(a=40, b=10, c=20, d=30)
        print(rr)

        # Generate a report
        report = epi.report(result, title="SEIR — Burkina Faso")
        report.save_html("report.html")

    ────────────────────────────────────────────────────
    GitHub : https://github.com/Xcept-Health/episia

Internal Functions
------------------

.. autofunction:: episia.__main__._supports_color
.. autofunction:: episia.__main__._render_logo
.. autofunction:: episia.__main__._print_doc
"""
setup.py - EpiTools package configuration.

Project layout: src/epitools/

Installation
------------
    pip install -e .                  # development (editable)
    pip install .                     # standard installation
    pip install epitools[full]        # all optional dependencies
    pip install epitools[dev]         # development tools
"""

from setuptools import setup, find_packages
from pathlib import Path

# ── Read README ───────────────────────────────────────────────────────────────
here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8") \
    if (here / "README.md").exists() else ""

# ── Read version from package __init__.py ────────────────────────────────────
version = {}
exec((here / "src" / "epitools" / "__init__.py").read_text(encoding="utf-8"), version)
__version__ = version.get("__version__", "0.1.0")

# ── Core dependencies ─────────────────────────────────────────────────────────

INSTALL_REQUIRES = [
    # Numerical computing
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "pandas>=1.5.0",

    # Interactive visualization (default backend)
    "plotly>=5.14.0",

    # Publication-quality visualization
    "matplotlib>=3.7.0",
]

# ── Optional dependencies ─────────────────────────────────────────────────────

EXTRAS_REQUIRE = {
    # Full install  all optional features
    "full": [
        "ipywidgets>=8.0.0",        # Interactive Jupyter dashboard
        "kaleido>=0.2.1",           # Plotly static export (PNG/SVG/PDF)
        "scikit-learn>=1.2.0",      # precision_recall_curve, roc_curve
        "seaborn>=0.12.0",          # Extended Matplotlib themes
        "openpyxl>=3.1.0",          # Excel read/write
        "tabulate>=0.9.0",          # Markdown table rendering in reports
    ],

    # Jupyter environment
    "jupyter": [
        "jupyter>=1.0.0",
        "ipywidgets>=8.0.0",
        "nbformat>=5.7.0",
    ],

    # Figure export
    "export": [
        "kaleido>=0.2.1",
        "pillow>=9.0.0",
    ],

    # Machine learning  calibration, ROC, precision-recall
    "ml": [
        "scikit-learn>=1.2.0",
    ],

    # Development & testing
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.4.0",
        "pre-commit>=3.3.0",
        "ipython>=8.0.0",
    ],

    # Documentation
    "docs": [
        "sphinx>=7.0.0",
        "sphinx-rtd-theme>=1.3.0",
        "myst-parser>=2.0.0",
        "nbsphinx>=0.9.0",
    ],
}

# Convenience alias  everything except dev/docs
EXTRAS_REQUIRE["all"] = list({
    dep
    for key in ("full", "jupyter", "export", "ml")
    for dep in EXTRAS_REQUIRE[key]
})

# ── Package setup ─────────────────────────────────────────────────────────────

setup(
    # ── Identity ──────────────────────────────────────────────────────────────
    name="epitools",
    version=__version__,
    author="Ariel Shadrac Ouedraogo",
    author_email="arielshadrac@gmail.com",
    maintainer="Xcept-Health",
    maintainer_email="arielshadrac@gmail.com",

    # ── Description ───────────────────────────────────────────────────────────
    description=(
        "Open-source Python epidemiology and biostatistics toolbox. "
        "Based on OpenEpi algorithms  risk ratios, odds ratios, sample size, "
        "diagnostic test evaluation, compartmental epidemic models (SIR/SEIR/SEIRD), "
        "Monte Carlo sensitivity analysis, surveillance data tools, and "
        "automated report generation. Built for the francophone African "
        "public health context."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",

    # ── URLs ──────────────────────────────────────────────────────────────────
    url="https://github.com/Xcept-Health/epitools",
    project_urls={
        "Bug Tracker":   "https://github.com/Xcept-Health/epitools/issues",
        "Documentation": "https://github.com/Xcept-Health/epitools#readme",
        "Source Code":   "https://github.com/Xcept-Health/epitools",
        "Organization":  "https://xcept-health.com",
    },

    # ── License ───────────────────────────────────────────────────────────────
    license="MIT",

    # ── Source layout: src/ ───────────────────────────────────────────────────
    package_dir={"": "src"},
    packages=find_packages(
        where="src",
        exclude=["tests*", "examples*", "docs*", "benchmarks*"],
    ),

    # ── Non-Python files ──────────────────────────────────────────────────────
    package_data={
        "epitools.viz": [
            "themes/*.mplstyle",
        ],
        "epitools": [
            "*.md",
            "*.txt",
            "*.yaml",
        ],
    },
    include_package_data=True,

    # ── Python version ────────────────────────────────────────────────────────
    python_requires=">=3.9",

    # ── Dependencies ──────────────────────────────────────────────────────────
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,

    # ── PyPI classifiers ──────────────────────────────────────────────────────
    classifiers=[
        # Development status
        "Development Status :: 3 - Alpha",

        # Target audience
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",

        # Domain
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Visualization",

        # License
        "License :: OSI Approved :: MIT License",

        # Platform
        "Operating System :: OS Independent",

        # Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",

        # Natural language
        "Natural Language :: English",
        "Natural Language :: French",
    ],

    # ── Keywords ──────────────────────────────────────────────────────────────
    keywords=[
        # Core discipline
        "epidemiology", "biostatistics", "public health",
        "OpenEpi", "outbreak analysis", "disease surveillance",

        # Statistical methods
        "risk ratio", "odds ratio", "relative risk",
        "confidence interval", "sample size", "statistical power",
        "sensitivity", "specificity", "ROC curve", "AUC",
        "Mantel-Haenszel", "stratified analysis",
        "logistic regression", "Poisson regression",

        # Epidemic modeling
        "SIR model", "SEIR model", "SEIRD",
        "compartmental model", "basic reproduction number", "R0",
        "herd immunity", "epidemic curve",
        "Monte Carlo", "sensitivity analysis", "calibration",

        # Context
        "Africa", "Burkina Faso", "francophone Africa",
        "DHIS2", "surveillance data", "attack rate",
        "endemic channel", "alert detection",
    ],

    # ── Future CLI entry point ────────────────────────────────────────────────
    entry_points={
        "console_scripts": [
            # "epitools = epitools.cli:main",  # planned for v0.2.0
        ],
    },

    # ── Misc ──────────────────────────────────────────────────────────────────
    zip_safe=False,
)
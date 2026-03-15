"""
setup.py - EpiTools package configuration.

Project layout: src/epitools/

Installation
------------
    pip install -e ".[dev]"           # development (editable)
    pip install -e "."                # editable without extras
    pip install ".[full]"             # all optional dependencies
"""

from setuptools import setup, find_packages
from pathlib import Path
import re

#  Read README 
here = Path(__file__).parent
long_description = (here / "README.md").read_text(encoding="utf-8") \
    if (here / "README.md").exists() else ""

#  Read version — regex only, no exec() 
# exec() would run the relative imports in __init__.py and crash during build.
_init_path = here / "src" / "epitools" / "__init__.py"
_init_text  = _init_path.read_text(encoding="utf-8") if _init_path.exists() else ""
_match      = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', _init_text, re.M)
__version__ = _match.group(1) if _match else "0.1.0-alpha"

#  Core dependencies 

INSTALL_REQUIRES = [
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "pandas>=1.5.0",
    "plotly>=5.14.0",
    "matplotlib>=3.7.0",
]

#  Optional dependencies 

EXTRAS_REQUIRE = {
    "full": [
        "ipywidgets>=8.0.0",
        "kaleido>=0.2.1",
        "scikit-learn>=1.2.0",
        "seaborn>=0.12.0",
        "openpyxl>=3.1.0",
        "tabulate>=0.9.0",
    ],
    "jupyter": [
        "jupyter>=1.0.0",
        "ipywidgets>=8.0.0",
        "nbformat>=5.7.0",
    ],
    "export": [
        "kaleido>=0.2.1",
        "pillow>=9.0.0",
    ],
    "ml": [
        "scikit-learn>=1.2.0",
    ],
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
    "docs": [
        "sphinx>=7.0.0",
        "sphinx-rtd-theme>=1.3.0",
        "myst-parser>=2.0.0",
        "nbsphinx>=0.9.0",
    ],
}

EXTRAS_REQUIRE["all"] = list({
    dep
    for key in ("full", "jupyter", "export", "ml")
    for dep in EXTRAS_REQUIRE[key]
})

#  Package setup 

setup(
    name="epitools",
    version=__version__,
    author="Fildouindé Ariel Shadrac Ouedraogo",
    author_email="arielshadrac@gmail.com",
    maintainer="Xcept-Health",
    maintainer_email="arielshadrac@gmail.com",

    description=(
        "Open-source Python epidemiology and biostatistics toolbox. "
        "Based on OpenEpi algorithms — risk ratios, odds ratios, sample size, "
        "diagnostic test evaluation, compartmental epidemic models (SIR/SEIR/SEIRD), "
        "Monte Carlo sensitivity analysis, surveillance data tools, and "
        "automated report generation. Built for the francophone African "
        "public health context."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",

    url="https://github.com/Xcept-Health/epitools",
    project_urls={
        "Bug Tracker":   "https://github.com/Xcept-Health/epitools/issues",
        "Documentation": "https://github.com/Xcept-Health/epitools#readme",
        "Source Code":   "https://github.com/Xcept-Health/epitools",
        "Organization":  "https://xcept-health.com",
    },

    license="MIT",

    # src/ layout
    package_dir={"": "src"},
    packages=find_packages(
        where="src",
        exclude=["tests*", "examples*", "docs*", "benchmarks*"],
    ),

    package_data={
        "epitools.viz": ["themes/*.mplstyle"],
        "epitools":     ["*.md", "*.txt", "*.yaml"],
    },
    include_package_data=True,

    python_requires=">=3.9",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Natural Language :: English",
        "Natural Language :: French",
    ],

    keywords=[
        "epidemiology", "biostatistics", "public health",
        "OpenEpi", "outbreak analysis", "disease surveillance",
        "risk ratio", "odds ratio", "confidence interval",
        "sample size", "sensitivity", "specificity", "ROC curve",
        "SIR model", "SEIR model", "SEIRD",
        "compartmental model", "R0", "herd immunity",
        "Monte Carlo", "calibration",
        "Africa", "Burkina Faso", "DHIS2", "surveillance data",
    ],

    entry_points={},
    zip_safe=False,
)
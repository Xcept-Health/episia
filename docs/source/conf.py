# Configuration file for Sphinx documentation.

project = "Episia"
author = "Fildouindé Ariel Shadrac OUEDRAOGO"
release = "0.1.1"
version = "0.1.1"

# Theme
html_theme = "pydata_sphinx_theme"

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',      # for Google and NumPy style docstrings
    'sphinx.ext.mathjax',       # for rendering math equations
    'sphinx.ext.intersphinx',   # for linking to external documentation
    'sphinx.ext.autosummary',   # for generating summary tables of modules/classes/functions
]

# Source
source_suffix = '.rst'
master_doc = 'index'

# HTML
html_static_path = ['_static']
html_logo = None
html_title = "Episia Documentation"

# Context for HTML templates
html_context = {
    "github_user": "Xcept-Health",
    "github_repo": "episia",
    "github_version": "main",
    "doc_path": "docs/source",
}

html_theme_options = {
    "github_url": "https://github.com/Xcept-Health/episia",
    "twitter_url": "https://twitter.com/xcept_health",
    "use_edit_page_button": True,
    "show_toc_level": 2,
}

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'plotly': ('https://plotly.com/python-api-reference/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
}
autodoc_typehints = 'description'

# define warnings to suppress
suppress_warnings = [
    'duplicate',
    'ref.term',
]
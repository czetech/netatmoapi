"""Sphinx configuration."""
from importlib.metadata import distribution

import netatmoapi

_dist = distribution(netatmoapi.__name__)
_author = _dist.metadata["Author"]

# Project information
project = "NetatmoAPI"
author = _author
copyright = f"2022, {_author}"
version = _dist.version

# General configuration
extensions = ["m2r2", "sphinx.ext.autodoc", "sphinx.ext.viewcode"]

# Options for HTML output
html_theme = "sphinx_rtd_theme"

# Options for extension sphinx.ext.autodoc
autodoc_member_order = "bysource"

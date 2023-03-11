#!/usr/bin/env python3
"""
Configuration for Sphinx.
"""

# pylint: disable=invalid-name

import datetime
import importlib.metadata

project = "VWS-Python"
author = "Adam Dangoor"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx-prompt",
    "sphinx_substitution_extensions",
    "sphinxcontrib.spelling",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

year = datetime.datetime.now(tz=datetime.UTC).year
project_copyright = f"{year}, {author}"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# Use ``importlib.metadata.version`` as per
# https://github.com/pypa/setuptools_scm#usage-from-sphinx.
version = importlib.metadata.version(distribution_name=project)
_month, _day, _year, *_ = version.split(".")
release = f"{_month}.{_day}.{_year}"

language = "en"

# The name of the syntax highlighting style to use.
pygments_style = "sphinx"

html_theme = "furo"
html_title = project
html_show_copyright = False
html_show_sphinx = False
html_show_sourcelink = False
html_theme_options = {
    "sidebar_hide_name": False,
}

# Output file base name for HTML help builder.
htmlhelp_basename = "VWSPYTHONdoc"
autoclass_content = "init"
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.11", None),
}
nitpicky = True
warning_is_error = True
nitpick_ignore = [
    ("py:class", "_io.BytesIO"),
    # Requests documentation exposes ``requests.Response``, not
    # ``requests.models.response``.
    ("py:class", "requests.models.Response"),
]


autoclass_content = "both"


# Don't check anchors because many websites use #! for AJAX magic
# http://sphinx-doc.org/config.html#confval-linkcheck_anchors
linkcheck_anchors = False
# Retry link checking to avoid transient network errors.
linkcheck_retries = 5
linkcheck_ignore = [
    # Requires login.
    r"https://developer.vuforia.com/targetmanager",
]

spelling_word_list_filename = "../../spelling_private_dict.txt"

autodoc_member_order = "bysource"

rst_prolog = f"""
.. |project| replace:: {project}
.. |release| replace:: {release}
.. |github-owner| replace:: VWS-Python
.. |github-repository| replace:: vws-python
"""

always_document_param_types = True

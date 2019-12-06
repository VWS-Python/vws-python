#!/usr/bin/env python3

"""
Configuration for Sphinx.
"""

# pylint: disable=invalid-name

import datetime
import os
import sys
from email import message_from_string
from pathlib import Path

import pkg_resources

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx_substitution_extensions',
    'sphinxcontrib.spelling',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

docs_source_dir = Path(__file__).parent
docs_dir = docs_source_dir.parent
repo_dir = docs_dir.parent
src_dir = repo_dir / 'src'
distributions = {v.key: v for v in set(pkg_resources.working_set)}
(distribution, ) = {
    dist
    for dist in distributions.values() if dist.location == str(src_dir)
}
project_name = distribution.project_name

pkg_info = distribution.get_metadata('PKG-INFO')
pkg_info_as_message = message_from_string(pkg_info)

project = pkg_info_as_message['Name']
author = pkg_info_as_message['Author']
year = datetime.datetime.now().year
copyright = f'{year}, {author}'  # pylint: disable=redefined-builtin

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = distribution.version
release = version.split('+')[0]

substitutions = [
    ('|release|', release),
    ('|github-owner|', 'adamtheturtle'),
    ('|github-repository|', 'vws-python'),
]

language = None

# The name of the syntax highlighting style to use.
pygments_style = 'sphinx'
html_theme = 'alabaster'

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ],
}

# Output file base name for HTML help builder.
htmlhelp_basename = 'VWSPYTHONdoc'
autoclass_content = 'init'
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.7', None),
}
nitpicky = True
warning_is_error = True
nitpick_ignore = [
    ('py:exc', 'RetryError'),
    # See https://bugs.python.org/issue31024 for why Sphinx cannot find this.
    ('py:class', 'typing.Tuple'),
    ('py:class', 'typing.Optional'),
    ('py:class', '_io.BytesIO'),
    ('py:class', 'docker.types.services.Mount'),
    # Requests documentation exposes ``requests.Response``, not
    # ``requests.models.response``.
    ('py:class', 'requests.models.Response'),
]

html_show_copyright = False
html_show_sphinx = False
html_show_sourcelink = False
autoclass_content = 'both'

html_theme_options = {
    'show_powered_by': 'false',
}

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
    ],
}

# Don't check anchors because many websites use #! for AJAX magic
# http://sphinx-doc.org/config.html#confval-linkcheck_anchors
linkcheck_anchors = False
# Retry link checking to avoid transient network errors.
linkcheck_retries = 5
linkcheck_ignore = [
    # Requires login.
    r'https://developer.vuforia.com/targetmanager',
]

spelling_word_list_filename = '../../spelling_private_dict.txt'

autodoc_member_order = 'bysource'

rst_prolog = f"""
.. |project| replace:: {project}
"""

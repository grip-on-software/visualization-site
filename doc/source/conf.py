"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# pylint: disable=invalid-name

import sys
import os

sys.path.append(os.path.abspath('_ext'))

project = 'Grip on Software'
project_copyright = '2017-2020 ICTU, 2017-2022 Leiden University, 2017-2024 Leon Helwerda'
author = 'Leon Helwerda'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx-jsonschema',
    'preprocess_replace'
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_copy_source = False
html_use_index = False
html_baseurl = 'https://gros.liacs.nl/schema/'
html_theme_options = {
    'body_max_width': '1146px',
    'page_width': '1366px'
}

# LaTeX output options
latex_elements = {
    'preamble': r'\setcounter{tocdepth}{2}'
}

# JSON schema options
jsonschema_options = {
    'lift_definitions': True,
    'auto_reference': True
}

# Replacements for schema paths/URLs
preprocess_replacements = {
    "|agent-config-schema|" : "https://gros.liacs.nl/schema/agent-config",
    "|data-analysis-schema|" : "https://gros.liacs.nl/schema/data-analysis",
    "|data-gathering-schema|" : "https://gros.liacs.nl/schema/data-gathering",
    "|data-gathering-compose-schema|": "https://gros.liacs.nl/schema/data-gathering-compose",
    "|deployer-schema|": "https://gros.liacs.nl/schema/deployer",
    "|export-exchange-schema|": "https://gros.liacs.nl/schema/export-exchange",
    "|monetdb-import-schema|": "https://gros.liacs.nl/schema/monetdb-import",
    "|prediction-schema|": "https://gros.liacs.nl/schema/prediction",
    "|visualization-schema|": "https://gros.liacs.nl/schema",
    "|visualization-site-schema|":
        "https://gros.liacs.nl/schema/visualization-site/schema/visualization-site",
    "|visualization-ui-schema|": "https://gros.liacs.nl/schema/visualization-ui"
}

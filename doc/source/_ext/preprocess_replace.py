"""
Replace some identifiers in the source files.
"""

def preprocess_replace(app, docname, source):
    """
    Replace identifiers.
    """

    result = source[0]
    for key in app.config.preprocess_replacements:
        result = result.replace(key, app.config.preprocess_replacements[key])
    source[0] = result

def setup(app):
    """
    Setup the extension.
    """

    app.add_config_value('preprocess_replacements', {}, True)
    app.connect('source-read', preprocess_replace)

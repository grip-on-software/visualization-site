Visualization site
------------------

These schemas define configuration for the hub and the visualizations available
in it.

.. jsonschema:: |visualization-site-schema|/config.json
   :auto_target: True
.. jsonschema:: |visualization-site-schema|/samples.json
.. jsonschema:: |visualization-site-schema|/visualizations.json

.. _metadata:

Visualization metadata
----------------------

These schemas are reusable specifications for localization and groups of
features, projects and source information. Multiple visualizations make use
of these formats to define translations and provide structured, navigable
and traceable data.

.. jsonschema:: |visualization-schema|/metadata/features.json
.. jsonschema:: |visualization-schema|/metadata/locale.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/metadata/projects.json
.. jsonschema:: |visualization-schema|/metadata/projects_meta.json
.. jsonschema:: |visualization-schema|/metadata/project_sources.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/metadata/projects_sources.json
.. jsonschema:: |visualization-schema|/metadata/sprint_sources.json

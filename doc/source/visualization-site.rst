Visualization site
------------------

These schemas define configuration for the hub and the visualizations available
in it.

.. jsonschema:: |visualization-site-schema|/config.json
   :auto_target: True
.. jsonschema:: |visualization-site-schema|/visualizations.json

Visualization metadata
----------------------

These schemas are reusable specifications for localization and groups of
features, projects and source information.

.. jsonschema:: |visualization-schema|/metadata/features.json
.. jsonschema:: |visualization-schema|/metadata/locale.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/metadata/projects.json
.. jsonschema:: |visualization-schema|/metadata/projects_meta.json
.. jsonschema:: |visualization-schema|/metadata/project_sources.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/metadata/projects_sources.json
.. jsonschema:: |visualization-schema|/metadata/sprint_sources.json

Visualization UI
----------------

This schema specifies navigation UI element format.

.. jsonschema:: |visualization-ui-schema|/navbar.json

Platform status
---------------

These schemas specify how the BigBoat status visualization is configured and
how the data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/bigboat-status/config.json
.. jsonschema:: |visualization-schema|/bigboat-status/durations.json
.. jsonschema:: |visualization-schema|/bigboat-status/fields.json
.. jsonschema:: |visualization-schema|/bigboat-status/project.json
.. jsonschema:: |visualization-schema|/bigboat-status/urls.json

Collaboration graph
-------------------

These schemas specify how the Collaboration graph visualization is configured
and how the data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/collaboration-graph/config.json
.. jsonschema:: |visualization-schema|/collaboration-graph/intervals.json
.. jsonschema:: |visualization-schema|/collaboration-graph/project_members.json

Heatmap
-------

These schemas specify how the Heatmap visualization is configured and how the
data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/heatmap/config.json
.. jsonschema:: |visualization-schema|/heatmap/volume.json
.. jsonschema:: |visualization-schema|/heatmap/weather.json

Leaderboard
-----------

These schemas specify how the Leaderboard visualization is configured and how
the data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/leaderboard/config.json
.. jsonschema:: |visualization-schema|/leaderboard/project_features.json
.. jsonschema:: |visualization-schema|/leaderboard/project_features_groups.json
.. jsonschema:: |visualization-schema|/leaderboard/project_features_links.json
.. jsonschema:: |visualization-schema|/leaderboard/project_features_normalize.json

Prediction site
---------------

These schemas specify how the prediction site is configured and how the data
used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/prediction-site/branches.json
.. jsonschema:: |visualization-schema|/prediction-site/config.json
.. jsonschema:: |visualization-schema|/prediction-site/configuration.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/prediction-site/sprint_prediction.json
.. jsonschema:: |visualization-schema|/prediction-site/sprints.json

Process flow
------------

These schemas specify how the Process flow visualization is configured and how
the data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/process-flow/config.json
.. jsonschema:: |visualization-schema|/process-flow/story_flow_palette.json
.. jsonschema:: |visualization-schema|/process-flow/story_flow_states.json

Sprint report
-------------

These schemas specify how the Sprint report visualization is configured and how
the data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/sprint-report/categories.json
.. jsonschema:: |visualization-schema|/sprint-report/config.json
.. jsonschema:: |visualization-schema|/sprint-report/expressions.json
.. jsonschema:: |visualization-schema|/sprint-report/features.json
.. jsonschema:: |visualization-schema|/sprint-report/metric_targets.json
.. jsonschema:: |visualization-schema|/sprint-report/sprints.json

Timeline
--------

These schemas specify how the Timeline visualization is configured and how the
data used by the visualization is formatted.

.. jsonschema:: |visualization-schema|/timeline/boards.json
.. jsonschema:: |visualization-schema|/timeline/config.json
.. jsonschema:: |visualization-schema|/timeline/data.json
.. jsonschema:: |visualization-schema|/timeline/event.json
   :auto_target: True
.. jsonschema:: |visualization-schema|/timeline/features.json
.. jsonschema:: |visualization-schema|/timeline/links.json
.. jsonschema:: |visualization-schema|/timeline/project_event.json
.. jsonschema:: |visualization-schema|/timeline/sprint_burndown.json
.. jsonschema:: |visualization-schema|/timeline/types.json

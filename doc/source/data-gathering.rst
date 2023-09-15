Data gatherer
-------------

This schema specifies some basic data types used across the data acquisition
component.

.. jsonschema:: |data-gathering-schema|/utils.json
   :auto_target: True

.. _controller:

Data gathering controller
-------------------------

These schemas specify formats of the controller involved in the data acquisition
component. The OpenAPI specification for the `data gathering controller API <https://gros.liacs.nl/swagger/?urls.primaryName=Data%20gathering%20controller%20API%20(view%20only)>`_
makes use of these schemas.

.. jsonschema:: |data-gathering-schema|/controller/access.json
.. jsonschema:: |data-gathering-schema|/controller/agent.json
.. jsonschema:: |data-gathering-schema|/controller/encrypt.json
.. jsonschema:: |data-gathering-schema|/controller/export.json
.. jsonschema:: |data-gathering-schema|/controller/log.json
.. jsonschema:: |data-gathering-schema|/controller/status.json
.. jsonschema:: |data-gathering-schema|/controller/version.json

.. _scraper:

Data gathering scraper
----------------------

These schemas specify formats of the agent involved in the data acquisition
component. The OpenAPI specification for the `data gathering scraper agent API <https://gros.liacs.nl/swagger/?urls.primaryName=Data%20gathering%20scraper%20agent%20API%20(view%20only)>`_
makes use of these schemas.

.. jsonschema:: |data-gathering-schema|/scraper/scrape.json
.. jsonschema:: |data-gathering-schema|/scraper/status.json

Data gathering formats
----------------------

These schemas specify formats of data acquired from various data sources, which
are made available for importing into a database.

.. _bigboat:

.. jsonschema:: |data-gathering-schema|/bigboat/status.json

.. _jenkins:

.. jsonschema:: |data-gathering-schema|/jenkins/statistics.json

.. _jira:

.. jsonschema:: |data-gathering-schema|/jira/comments.json
.. jsonschema:: |data-gathering-schema|/jira/component.json
.. jsonschema:: |data-gathering-schema|/jira/developer.json
.. jsonschema:: |data-gathering-schema|/jira/fields.json
.. jsonschema:: |data-gathering-schema|/jira/issue.json
.. jsonschema:: |data-gathering-schema|/jira/issue_component.json
.. jsonschema:: |data-gathering-schema|/jira/issuelinks.json
.. jsonschema:: |data-gathering-schema|/jira/issuetype.json
.. jsonschema:: |data-gathering-schema|/jira/priority.json
.. jsonschema:: |data-gathering-schema|/jira/ready_status.json
.. jsonschema:: |data-gathering-schema|/jira/relationshiptype.json
.. jsonschema:: |data-gathering-schema|/jira/resolution.json
.. jsonschema:: |data-gathering-schema|/jira/sprint.json
.. jsonschema:: |data-gathering-schema|/jira/status.json
.. jsonschema:: |data-gathering-schema|/jira/status_category.json
.. jsonschema:: |data-gathering-schema|/jira/subtasks.json
.. jsonschema:: |data-gathering-schema|/jira/test_execution.json
.. jsonschema:: |data-gathering-schema|/jira/version.json

.. _ldap:

.. jsonschema:: |data-gathering-schema|/ldap/members.json

.. _project:

.. jsonschema:: |data-gathering-schema|/project/environments.json
.. jsonschema:: |data-gathering-schema|/project/metadata.json
.. jsonschema:: |data-gathering-schema|/project/sources.json
   :auto_target: True

.. _quality:

.. jsonschema:: |data-gathering-schema|/quality/compact_history.json
.. jsonschema:: |data-gathering-schema|/quality/history_update.json
.. jsonschema:: |data-gathering-schema|/quality/hqlib_targets.json
.. jsonschema:: |data-gathering-schema|/quality/hqlib_targets_update.json
.. jsonschema:: |data-gathering-schema|/quality/metric_base_names.json
.. jsonschema:: |data-gathering-schema|/quality/metric_names.json
   :auto_target: True
.. jsonschema:: |data-gathering-schema|/quality/metric_targets.json
   :auto_target: True
.. jsonschema:: |data-gathering-schema|/quality/metric_versions.json
.. jsonschema:: |data-gathering-schema|/quality/metrics.json
.. jsonschema:: |data-gathering-schema|/quality/update.json

.. _seats:

.. jsonschema:: |data-gathering-schema|/seats/config.json
.. jsonschema:: |data-gathering-schema|/seats/counts.json
.. jsonschema:: |data-gathering-schema|/seats/update.json

.. _tfs:

.. jsonschema:: |data-gathering-schema|/tfs/developer.json
.. jsonschema:: |data-gathering-schema|/tfs/fields.json
.. jsonschema:: |data-gathering-schema|/tfs/sprint.json
.. jsonschema:: |data-gathering-schema|/tfs/team.json
.. jsonschema:: |data-gathering-schema|/tfs/team_member.json
.. jsonschema:: |data-gathering-schema|/tfs/tfs_update.json
.. jsonschema:: |data-gathering-schema|/tfs/work_item.json

.. _topdesk:

.. jsonschema:: |data-gathering-schema|/topdesk/reservations.json

.. _vcs:

.. jsonschema:: |data-gathering-schema|/vcs/change_path.json
.. jsonschema:: |data-gathering-schema|/vcs/commit_comment.json
.. jsonschema:: |data-gathering-schema|/vcs/github_issue.json
.. jsonschema:: |data-gathering-schema|/vcs/github_issue_note.json
.. jsonschema:: |data-gathering-schema|/vcs/github_repo.json
.. jsonschema:: |data-gathering-schema|/vcs/github_update.json
.. jsonschema:: |data-gathering-schema|/vcs/gitlab_repo.json
.. jsonschema:: |data-gathering-schema|/vcs/gitlab_update.json
.. jsonschema:: |data-gathering-schema|/vcs/latest_vcs_versions.json
.. jsonschema:: |data-gathering-schema|/vcs/merge_request.json
.. jsonschema:: |data-gathering-schema|/vcs/merge_request_note.json
.. jsonschema:: |data-gathering-schema|/vcs/merge_request_review.json
.. jsonschema:: |data-gathering-schema|/vcs/tag.json
.. jsonschema:: |data-gathering-schema|/vcs/vcs_event.json
.. jsonschema:: |data-gathering-schema|/vcs/vcs_versions.json

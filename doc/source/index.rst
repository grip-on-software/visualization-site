****************
Grip on Software
****************

The following documentation introduces the JSON schema specifications of various
exchange formats used by the Grip on Software data acquisition pipeline.

`JSON Schema <https://json-schema.org/>`_ is a specific format that describes the structure of JSON and YAML documents, such as what types they can contain.
This allows those documents to be validated for compatibility with the specific
module or component that uses the data. Additionally, through documentation,
these structures become reusable and more easily extensible.

Schemas
=======

.. toctree::
   :maxdepth: 2

   data-gathering
   agent-config
   data-gathering-compose
   deployer
   monetdb-import
   export-exchange
   data-analysis
   prediction
   visualization-site

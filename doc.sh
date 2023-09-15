#!/bin/bash
# Perform a documentation build of the schemas in HTML format.
#
# Copyright 2017-2020 ICTU
# Copyright 2017-2022 Leiden University
# Copyright 2017-2023 Leon Helwerda
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

target=html
if [ ! -z $1 ]; then
    target=$1
    shift
fi
paths=$*

if [[ -z $JENKINS_HOME && -z $paths ]]; then
    echo "Usage: $0 [target] [paths...]" >&2
    echo "This script must either run in a Jenkins context or be given paths" >&2
    exit 1
fi

# Repositories that have JSON schemas and a Jenkins build that archives them.
ARCHIVE_NAMES="visualization-site prediction data-analysis monetdb-import export-exchange deployer data-gathering data-gathering-compose agent-config"
# Subset of repositories that have nested schema directories.
NESTED_NAMES="data-gathering"
# Repositories that are provided as an NPM package under the @gros scope with
# packaged JSON schemas in them.
MODULE_NAMES="visualization-ui"

# Defines for sphinx-build to replace schema URLs
DEFINES=""
# All the schemafiles
SCHEMAS=""
for repo in $ARCHIVE_NAMES; do
    if [ -z "$JENKINS_HOME" ]; then
        schema=""
        for prefix in $paths; do
            if [ -d "$prefix/$repo/schema" ]; then
                schema="$prefix/$repo/schema"
                break
            fi
        done
        if [ -z "$schema" ]; then
            echo "Could not find a schema path for repo $repo" >&2
            exit 1
        fi
    else
        job="build-$repo"
        build="lastSuccessfulBuild"
        branch="master"
        if [[ $repo == "prediction" ]]; then
            job="create-$repo"
            # Prediction builds do not archive artifacts if they are UNSTABLE
            build="lastStableBuild"
        elif [[ $repo == "visualization-site" ]]; then
            if [[ ! -z "$BRANCH_NAME" && $PUBLISH_PRODUCTION == "true" ]]; then
                branch="$BRANCH_NAME"
            fi
        fi
        path="$JENKINS_HOME/jobs/$job/branches/$branch"
        # Retrieve most recent build (even if tests make it UNSTABLE)
        if [[ $repo == "visualization-site" && ! -z "$BUILD_NUMBER" ]]; then
            ID=$BUILD_NUMBER
        else
            ID=$(sed -n "/$build /s/$build //p" $path/builds/permalinks)
        fi
        schema="$path/builds/$ID/archive/schema"
    fi

    if [[ $repo == "visualization-site" ]]; then
        DEFINES="$DEFINES -D 'preprocess_replacements.|$repo-schema|=$schema/visualization-site' -D 'preprocess_replacements.|visualization-schema|=$schema'"
        SCHEMAS="$SCHEMAS $schema/*/*.json"
    else
        if [[ " $NESTED_NAMES " =~ " $repo " ]]; then
            SCHEMAS="$SCHEMAS $schema/*.json $schema/*/*.json"
        else
            SCHEMAS="$SCHEMAS $schema/*.json"
        fi
        DEFINES="$DEFINES -D 'preprocess_replacements.|$repo-schema|=$schema'"
    fi
done

for module in $MODULE_NAMES; do
    if [ ! -d "$PWD/node_modules/@gros/$module/schema" ]; then
        echo "Could not find a schema path for module $module" >&2
        exit 1
    fi
    DEFINES="$DEFINES -D 'preprocess_replacements.|$module-schema|=$PWD/node_modules/@gros/$module/schema'"
    SCHEMAS="$SCHEMAS $PWD/node_modules/@gros/$module/schema/*.json"
done

# Validate all schemas
echo "Performing schema validation"
check-jsonschema --check-metaschema $SCHEMAS

# Loops over each sample glob path and schema URI in tests/schema-samples.json
# Then run:
# check-jsonschema --schemafile $SCHEMA --base-uri $PATH_TO_SCHEMA_DIR $PATHS
jq -r "to_entries|map(\"check-jsonschema --schemafile file://$PWD/schema/\(.value) --base-uri file://$PWD/schema/\(.value[0:.value | split(\"#\") | .[0] | rindex(\"/\")])/ test/sample/\(.key)\")|.[]" test/schema-samples.json | sh -x -

cd doc && SPHINXOPTS=$DEFINES make $target

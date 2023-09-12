#!/bin/bash -e
# Copy visualization artifacts to a published site for direct access.
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

if [ -z "$VISUALIZATION_NAMES" ]; then
    VISUALIZATION_NAMES=$(cat visualization_names.txt)
fi

CONFIG="config.json"
if [ ! -z "$VISUALIZATION_SITE_CONFIGURATION" ]; then
    CONFIG="$VISUALIZATION_SITE_CONFIGURATION"
fi
if [ ! -f "$CONFIG" ]; then
    CONFIG="lib/config.json"
fi
if [ -z "$JENKINS_HOME" ]; then
    echo "This script can only be run in a Jenkins context"
    exit 1
fi
JOBS_PATH="$JENKINS_HOME/jobs"
TARGET=$(jq -r .jenkins_direct $CONFIG)
COPY="rsync -au --delete --exclude htmlpublisher-wrapper.html"
COPY_APPEND="rsync -au --exclude htmlpublisher-wrapper.html"

if [[ "$TARGET" == "" || "$TARGET" == "null" ]]; then
    echo "No target for copy specified"
    echo "To run copy.sh, set 'jenkins_direct' in $CONFIG to a path"
    exit 0
fi

# Repositories that have JSON schemas and a Jenkins build that archives them.
ARCHIVE_NAMES="visualization-site prediction data-analysis monetdb-import export-exchange deployer data-gathering data-gathering-compose agent-config"
# Subset of repositories that have openapi.json files in subdirectories and
# a Jenkins build that archives them, excluding visualization-site.
OPENAPI_NAMES="data-gathering export-exchange"
# Repositories that are provided as an NPM package under the @gros scope with
# packaged JSON schemas in them.
MODULE_NAMES="visualization-ui"
# Repositories whose visualizations are available from their respective `_url`
# paths, rather than a subpath of their repository name.
ROOT_NAMES="visualization-site prediction-site"

# Copy published visualization HTML and prediction/schema artifacts
for repo in $VISUALIZATION_NAMES $ARCHIVE_NAMES; do
    job="build-$repo"
    branches="*master"
    build="lastSuccessfulBuild"
    if [[ $repo == "prediction" ]]; then
        config="prediction"
        job="create-$repo"
        # Include all branches
        branches="*"
        # Prediction builds do not archive new artifacts if they are UNSTABLE
        build="lastStableBuild"
    elif [[ $repo == "prediction-site" ]]; then
        default_organization="combined"
        config="prediction"
    elif [[ $repo == "visualization-site" ]]; then
        default_organization="combined"
        if [[ ! -z "$BRANCH_NAME" && $PUBLISH_PRODUCTION == "true" ]]; then
            branches="$BRANCH_NAME"
        fi
    else
        default_organization=$(jq -r ".hub_mapping.hub.organization.default // \"combined\"" $CONFIG)
        config="visualization"
    fi

    for path in $JOBS_PATH/$job/branches/$branches; do
        # Retrieve most recent build (even if tests make it UNSTABLE)
        if [[ $repo == "visualization-site" && ! -z "$BUILD_NUMBER" ]]; then
            ID=$BUILD_NUMBER
        else
            ID=$(sed -n "/$build /s/$build //p" $path/builds/permalinks)
        fi
        branch=$(basename $path)
        if [[ $branch == "master" ]]; then
            organization=$default_organization
            publish_archive=1
        elif [[ $PUBLISH_PRODUCTION == "true" && ! -z "$BRANCH_NAME" && $branch == "$BRANCH_NAME" ]]; then
            organization="combined"
            publish_archive=1
        else
            organization=$(jq -r ".hub_organizations | .[] | select(.[\"$config-site\"] == \"$branch\") | .organization" $CONFIG)
            publish_archive=0
        fi
        # Convert/extract path from visualization/prediction URL
        # - Select proper organization
        # - Retrieve pathname from URL
        url="$(jq -r .${config}_url $CONFIG | sed -e s/\\\(\\/*\\\)\$organization/\\1$organization/)"
        target="$(echo 'const {URL} = require("node:url");process.stdout.write((new URL(process.argv[2], "http://example.org")).pathname)' | node - $url)"
        # Path to the publishable visualization ($VISUALIZATION_NAMES and hub)
        origin="$path/builds/$ID/htmlreports/Visualization"
        # Path to the archived files ($ARCHIVE_NAMES and prediction)
        archive="$path/builds/$ID/archive"
        if [ ! -d "$origin" ]; then
            origin="$path/htmlreports/Visualization/"
        fi
        if [[ " $ROOT_NAMES " =~ " $repo " ]]; then
            # Visualization-site and prediction-site from their root paths.
            mkdir -p "$TARGET/$target"
            $COPY_APPEND "$origin/" "$TARGET/$target"
        elif [[ $repo == "prediction" ]]; then
            # Prediction data
            mkdir -p "$TARGET/$repo/$branch/output"
            $COPY "$archive/output/" "$TARGET/$repo/$branch/output"
        elif [[ " $VISUALIZATION_NAMES " =~ " $repo " ]]; then
            mkdir -p "$TARGET/$target/$repo"
            $COPY "$origin/" "$TARGET/$target/$repo"
        fi

        if [[ $publish_archive == 1 && " $ARCHIVE_NAMES " =~ " $repo " ]]; then
            if [[ " $OPENAPI_NAMES " =~ " $repo " ]]; then
                # Convert archive paths to OpenAPI specifications to file names
                # that do not conflict with other repos/paths.
                # Repository: data-gathering
                # Archive name: scraper/agent/openapi.json
                # Publish name: data-gathering-scraper-agent-openapi.json
                find "$archive" -name "openapi.json" -exec bash -c 'echo ${0##"$1"} | sed -e "s/\//-/g" -e "s/^/${2//\//\\/}/" | xargs cp "$0"' {} "$archive/" "$TARGET/$repo-" \;
            fi
            if [[ $repo == "visualization-site" ]]; then
                cp "$archive/openapi.json" "$TARGET/openapi.json"
                mkdir -p "$TARGET/schema"
                $COPY_APPEND "$archive/schema/" "$TARGET/schema/"
                $COPY_APPEND "$path/htmlreports/Documentation/" "$TARGET/schema/"

                # Standalone Swagger
                COMPOSE_ARGS="-f swagger/docker-compose.yml"
                docker compose $COMPOSE_ARGS up -d --wait --force-recreate
                SWAGGER_CONTAINER=$(docker compose $COMPOSE_ARGS ps -q swagger)
                if [ -z "$SWAGGER_CONTAINER" ]; then
                    echo "Could not bring up Swagger instances." >&2
                    exit 1
                fi
                docker compose $COMPOSE_ARGS cp swagger:/usr/share/nginx/html/ "swagger/dist/"
                docker compose $COMPOSE_ARGS down

                mkdir -p "$TARGET/swagger"
                $COPY "swagger/dist/" "$TARGET/swagger/"
            else
                mkdir -p "$TARGET/schema/$repo"
                $COPY "$archive/schema/" "$TARGET/schema/$repo"
            fi
        fi
    done
done
for module in $MODULE_NAMES; do
    $COPY "./node_modules/@gros/$module/schema/" "$TARGET/schema/$module"
done

# Download prediction branches
curl -g -H 'Accept: application/json' \
    -H "Authorization: Basic $(jq -r .jenkins_api_token $CONFIG)" \
    --cacert $(jq -r .jenkins_direct_cert $CONFIG) \
    "$(jq -r .jenkins_direct_url $CONFIG)/job/create-prediction/api/json?tree=jobs[name,lastStableBuild[description,duration,timestamp]]" > "$TARGET/branches.json"

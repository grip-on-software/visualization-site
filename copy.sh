#!/bin/bash -e
# Copy visualization artifacts to a published site for direct access.
#
# Copyright 2017-2020 ICTU
# Copyright 2017-2022 Leiden University
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
if [ ! -f "$CONFIG" ]; then
    CONFIG="lib/config.json"
fi
JOBS_PATH="$JENKINS_HOME/jobs"
TARGET=$(jq -r .jenkins_direct $CONFIG)
COPY="rsync -au --delete"
COPY_APPEND="rsync -au"

if [[ "$TARGET" == "" || "$TARGET" == "null" ]]; then
    echo "No target for copy specified"
    exit 0
fi

# Repositories that have JSON schemas and a Jenkins build that archives them.
ARCHIVE_NAMES="prediction monetdb-import export-exchange deployer data-gathering data-gathering-compose agent-config visualization-site"

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
        else
            organization=$(jq -r ".hub_organizations | .[] | select(.[\"$config-site\"] == \"$branch\") | .organization" $CONFIG)
        fi
        target="$(jq -r .${config}_url $CONFIG | sed -e s/\\/*\$organization/$organization/)"
        origin="$path/builds/$ID/htmlreports/Visualization"
        if [ ! -d "$origin" ]; then
            origin="$path/htmlreports/Visualization/"
        fi
        if [[ $repo == "visualization-site" ]]; then
            mkdir -p "$TARGET/$target"
            $COPY_APPEND "$origin/" "$TARGET/$target"
        elif [[ $repo == "prediction" ]]; then
            $COPY "$path/builds/$ID/archive/output/" "$TARGET/$repo/$branch/output"
        elif [[ " $VISUALIZATION_NAMES " =~ " $repo " ]]; then
            mkdir -p "$TARGET/$target"
            $COPY "$origin" "$TARGET/$target"
        fi

        if [[ $branch == "master" && " $ARCHIVE_NAMES " =~ " $repo " ]]; then
            if [[ $repo == "visualization-site" ]]; then
                cp "$path/builds/$ID/archive/openapi.json" "$TARGET/openapi.json"
                $COPY_APPEND "$path/builds/$ID/archive/schema" "$TARGET/schema"
            else
                mkdir -p "$TARGET/schema/$repo"
                $COPY "$path/builds/$ID/archive/schema/" "$TARGET/schema/$repo"
            fi
        fi
    done
done

# Download prediction branches
curl -g -H 'Accept: application/json' \
    -H "Authorization: Basic $(jq -r .jenkins_api_token $CONFIG)" \
    --cacert $(jq -r .jenkins_direct_cert $CONFIG) \
    "$(jq -r .jenkins_direct_url $CONFIG)/job/create-prediction/api/json?tree=jobs[name,lastStableBuild[description,duration,timestamp]]" > "$TARGET/branches.json"

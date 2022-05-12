#!/bin/bash
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

if [[ "$TARGET" == "" || "$TARGET" == "null" ]]; then
    echo "No target for copy specified"
    exit 0
fi

for visualization in $VISUALIZATION_NAMES visualization-site; do
    for path in $JOBS_PATH/build-$visualization/branches/*master; do
		# Retrieve most recent build (even if tests make it UNSTABLE)
        ID=$(sed -n "/lastSuccessfulBuild /s/lastSuccessfulBuild //p" $path/builds/permalinks)
        branch=$(basename $path)
        mkdir -p "$TARGET/$branch/"
        if [ -d "$path/builds/$ID/htmlreports/Visualization" ]; then
            $COPY "$path/builds/$ID/htmlreports/Visualization/" "$TARGET/$branch/$visualization/"
        else
            $COPY "$path/htmlreports/Visualization/" "$TARGET/$branch/$visualization/"
        fi
    done
done

curl -g -H 'Accept: application/json' \
    -H "Authorization: Basic $(jq -r .jenkins_api_token $CONFIG)" \
    --cacert $(jq -r .jenkins_direct_cert $CONFIG) \
    "$(jq -r .jenkins_direct_url $CONFIG)/job/create-prediction/api/json?tree=jobs[name,lastStableBuild[description,duration,timestamp]]" > "$TARGET/branches.json"

for path in $JOBS_PATH/create-prediction/branches/*; do
	# Prediction builds do not archive new artifacts in they are UNSTABLE
    ID=$(sed -n "/lastStableBuild /s/lastStableBuild //p" $path/builds/permalinks)
    branch=$(basename $path)
    mkdir -p "$TARGET/$branch/"
    $COPY "$path/builds/$ID/archive/" "$TARGET/$branch/prediction/"
done

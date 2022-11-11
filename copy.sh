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

for visualization in $VISUALIZATION_NAMES prediction visualization-site; do
	job="build-$visualization"
	branches="*master"
	build="lastSuccessfulBuild"
	if [[ $visualization == "prediction" ]]; then
		config="prediction"
		job="create-$visualization"
		# Include all branches
		branches="*"
		# Prediction builds do not archive new artifacts if they are UNSTABLE
		build="lastStableBuild"
	elif [[ $visualization == "prediction-site" ]]; then
		default_organization="combined"
		config="prediction"
	elif [[ $visualization == "visualization-site" ]]; then
		default_organization="combined"
	else
		default_organization=$(jq -r ".hub_mapping.hub.organization.default // \"combined\"" $CONFIG)
		config="visualization"
	fi

    for path in $JOBS_PATH/$job/branches/$branches; do
		# Retrieve most recent build (even if tests make it UNSTABLE)
        ID=$(sed -n "/$build /s/$build //p" $path/builds/permalinks)
        branch=$(basename $path)
		if [[ $branch == "master" ]]; then
			organization=$default_organization
		else
			organization=$(jq -r ".hub_organizations | .[] | select(.[\"$config-site\"] == \"$branch\") | .organization" $CONFIG)
		fi
		target="$(jq -r .${config}_url $CONFIG | sed -e s/\\/*\$organization/$organization/)"
        mkdir -p "$TARGET/$target"
		origin="$path/builds/$ID/htmlreports/Visualization"
        if [ ! -d "$origin" ]; then
			origin="$path/htmlreports/Visualization/"
		fi
		if [[ $visualization == "visualization-site" ]]; then
            $COPY_APPEND "$origin/" "$TARGET/$target"
		elif [[ $visualization == "prediction" ]]; then
			$COPY "$path/builds/$ID/archive/" "$TARGET/prediction/$branch"
        else
            $COPY "$origin" "$TARGET/$target"
        fi
    done
done

curl -g -H 'Accept: application/json' \
    -H "Authorization: Basic $(jq -r .jenkins_api_token $CONFIG)" \
    --cacert $(jq -r .jenkins_direct_cert $CONFIG) \
    "$(jq -r .jenkins_direct_url $CONFIG)/job/create-prediction/api/json?tree=jobs[name,lastStableBuild[description,duration,timestamp]]" > "$TARGET/branches.json"

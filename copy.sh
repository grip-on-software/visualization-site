#!/bin/bash

if [ -z "$VISUALIZATION_NAMES" ]; then
	VISUALIZATION_NAMES=$(cat visualization_names.txt)
fi

CONFIG="config.json"
if [ ! -f "$CONFIG" ]; then
    CONFIG="lib/config.json"
fi
JOBS_PATH="$JENKINS_HOME/jobs"
TARGET=$(jq -r .jenkins_direct $CONFIG)

if [[ "$TARGET" == "" || "$TARGET" == "null" ]]; then
    echo "No target for copy specified"
    exit 0
fi

for visualization in $VISUALIZATION_NAMES visualization-site; do
    for path in $JOBS_PATH/build-$visualization/branches/*master; do
        ID=$(sed -n "/lastSuccessfulBuild /s/lastSuccessfulBuild //p" $path/builds/permalinks)
        branch=$(basename $path)
        mkdir -p "$TARGET/$branch/"
        rm -rf "$TARGET/$branch/$visualization/"
        if [ -d "$path/builds/$ID/htmlreports/Visualization" ]; then
            cp -r "$path/builds/$ID/htmlreports/Visualization/" "$TARGET/$branch/$visualization/"
        else
            cp -r "$path/htmlreports/Visualization/" "$TARGET/$branch/$visualization/"
        fi
    done
done

curl -g -H 'Accept: application/json' \
    -H "Authorization: Basic $(jq -r .jenkins_api_token $CONFIG)" \
    --cacert $(jq -r .jenkins_direct_cert $CONFIG) \
    "$(jq -r .jenkins_direct_url $CONFIG)/job/create-prediction/api/json?tree=jobs[name,color,lastSuccessfulBuild[timestamp]]" > "$TARGET/branches.json"

for path in $JOBS_PATH/create-prediction/branches/*; do
    ID=$(sed -n "/lastSuccessfulBuild /s/lastSuccessfulBuild //p" $path/builds/permalinks)
    branch=$(basename $path)
    mkdir -p "$TARGET/$branch/"
    rm -rf "$TARGET/$branch/prediction/"
    cp -r "$path/builds/$ID/archive/" "$TARGET/$branch/prediction/"
done

#!/bin/bash
# Perform integration tests of visualizations using a virtualized network setup.
# This script handles the repository updates of the visualizations under test,
# Docker compose network setup/teardown, additional dependency installation,
# waiting for builds, logging/publishing results. During the integration tests,
# code coverage of the JavaScript of the visualizations is tracked and collected
# into a combined report, Docker/browser logs/screenshots are captured and
# finally security tests are performed for the dependencies.
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

if [ -z "$VISUALIZATION_SITE_CONFIGURATION" ]; then
    VISUALIZATION_SITE_CONFIGURATION="config.json"
fi
if [ ! -f "$VISUALIZATION_SITE_CONFIGURATION" ]; then
    VISUALIZATION_SITE_CONFIGURATION="lib/config.json"
fi

# Comparable integer format for versions - https://stackoverflow.com/a/37939589
function version() {
	echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }';
}

COMPOSE_ARGS="-p ${BUILD_TAG:-visualization} -f caddy/docker-compose.yml -f test/docker-compose.yml"

function container_logs() {
	echo $'<h2>Docker container logs</h2>\n<ul>' >> test/results/index.html

	docker compose $COMPOSE_ARGS ps -aq | xargs -L 1 -I {} /bin/bash -c '
		host=$(docker inspect --format="{{index .Config.Labels \"com.docker.compose.service\"}}.{{.Config.Domainname}}" {})
		state=$(docker inspect --format="{{.State.Status}}" {})
		docker inspect --format="$(cat log-format.txt)" {} > test/results/logs_$host.html
		echo "<pre>" >> test/results/logs_$host.html
		docker logs {} 2>&1 | sed "s/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g" >> test/results/logs_$host.html 2>&1
		echo -e "</pre>\n</body>\n</html>" >> test/results/logs_$host.html
		echo "<li><a href=\"logs_$host.html\" title=\"Logs for $(docker inspect --format={{.Name}} {})\">$host ($(docker logs {} 2>&1 | wc -c) bytes, end state: $state)</a></li>" >> test/results/index.html'

	echo $'</ul>\n</body>\n</html>' >> test/results/index.html
}

rm -rf test/junit test/results test/accessibility test/coverage test/downloads test/owasp-dep
mkdir -p repos
mkdir -p test/junit test/results test/accessibility test/coverage/output test/downloads
mkdir -p -m 0777 "$HOME/OWASP-Dependency-Check/data/cache"
mkdir -p -m 0777 test/owasp-dep

if [ -z "$REPO_ROOT" ]; then
	REPO_ROOT="repos"
else
	has_repo_root=1
fi

if [ -z "$VISUALIZATION_NAMES" ]; then
	VISUALIZATION_NAMES=$(cat visualization_names.txt)
fi

VISUALIZATION_ENV=$(env -i VISUALIZATION_ORGANIZATION=$VISUALIZATION_ORGANIZATION VISUALIZATION_COMBINED=$VISUALIZATION_COMBINED)

function reset_modules_volume() {
	# For the given visualization repository name, remove any running/stopped
	# containers that are still using the old volume, then remove the volume
	# itself. Finally, recreate the module for reuse in the Compose network.
	repo=$1
	docker ps -q -a --filter "volume=$BRANCH_NAME-$repo-modules" | xargs --no-run-if-empty docker rm -f
	docker volume rm -f "$BRANCH_NAME-$repo-modules"
	docker volume create "$BRANCH_NAME-$repo-modules"
}

function update_repo() {
	# Path to check out the repository to
	tree=$1
	shift
	# URL from which to obtain the remote repository
	url=$1
	shift
	# Visualization repository name; enables build check/module cleanup if given
	repo=$1
	if [ ! -d $tree ]; then
		echo "Cloning $tree"
		git clone $url $tree
		if [ ! -z "$repo" ]; then
			reset_modules_volume "$repo"
		fi
	elif [ ! -z "$has_repo_root" ]; then
		echo "Keeping $tree intact"
		if [ -d "$tree/node_modules" ]; then
			mv "$tree/node_modules" "$tree/node_modules.bak"
		fi
	else
		echo "Updating $tree"
		if [ -f "$tree/.gitattributes" ]; then
			GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rm .gitattributes
			GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git add -A
		fi
		if [ -f "$tree/.skip_build" ]; then
			previous_env=$(cat "$tree/.skip_build")
		else
			previous_env="no previous build"
		fi
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git reset --hard
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git remote set-url origin $url
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git fetch origin master
		LOCAL_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse HEAD)
		REMOTE_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse FETCH_HEAD)
		if [ ! -z "$repo" ] && [ $LOCAL_REV = $REMOTE_REV ] && [ "$VISUALIZATION_ENV" = "$previous_env" ] && [ ! -z $(docker volume ls -q -f "name=^$BRANCH_NAME-$repo-modules$") ]; then
			echo "$repo is up to date, skipping build in instance."
			echo "$VISUALIZATION_ENV" > "$tree/.skip_build"
		else
			GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git pull origin master
			if [ ! -z "$repo" ]; then
				echo "Build of $repo required"
				rm -f "$tree/.skip_build"
				reset_modules_volume "$repo"
			fi
		fi
	fi
}

for repo in $VISUALIZATION_NAMES; do
	tree="$PWD/$REPO_ROOT/$repo"
	url=$(git config --get remote.origin.url | sed s/visualization-site/$repo/)
	update_repo "$tree" "$url" "$repo"
	mkdir -p "$tree/public"
done

if [ -d "$PWD/$REPO_ROOT/prediction-site" ]; then
	tree="$PWD/$REPO_ROOT/prediction-site"
	sed -e "s/\\(\"visualization_url\"\\):\\s\\+\"\\//\\1: \"http:\\/\\/$(jq -r .visualization_server $VISUALIZATION_SITE_CONFIGURATION)\\//" $PREDICTION_CONFIGURATION > test/prediction-config.json
	cmp -s test/prediction-config.json "$tree/config.json"
	if [ $? -ne 0 ]; then
		echo "Including new configuration file for prediction-site (rebuild)"
		cp -f --no-preserve=mode,ownership test/prediction-config.json "$tree/config.json"
		rm -f "$tree/.skip_build"
	fi
	rm -rf "$tree/test"
	mkdir -p "$tree/test/junit" "$tree/test/coverage/output" "$tree/test/suite"
	mkdir -p -m 0777 "$tree/test/owasp-dep"
fi

PROXY_HOST=proxy

docker compose $COMPOSE_ARGS pull
docker compose $COMPOSE_ARGS up -d --force-recreate

TEST_CONTAINER=$(docker compose $COMPOSE_ARGS ps -q runner)
if [ -z "$TEST_CONTAINER" ]; then
	container_logs
	echo "Could not bring up the test instances." >&2
	exit 1
fi

echo "Instances are up, performing installations"
docker exec $TEST_CONTAINER pip install -r /work/requirements.txt

# Total time allocated for starting the visualizations
if [ -z "$VISUALIZATION_MAX_SECONDS" ]; then
	VISUALIZATION_MAX_SECONDS=60
fi
seconds=0
for name in $VISUALIZATION_NAMES; do
	container=$(docker compose $COMPOSE_ARGS ps -aq $name)
	if [ -z "$container" ]; then
		docker compose $COMPOSE_ARGS ps -a
		container_logs
		docker compose $COMPOSE_ARGS down
		echo "Could not find instance for $name." >&2
		exit 1
	fi

	running="true"
	while [ "$running" == "true" ]; do
		if [ $seconds -gt $VISUALIZATION_MAX_SECONDS ]; then
			container_logs
			docker compose $COMPOSE_ARGS down
			echo "$name did not seem to be done after ${VISUALIZATION_MAX_SECONDS}s." >&2
			exit 1
		fi

		# Check if the visualization is done building
		running=$(docker inspect -f '{{.State.Running}}' $container 2>&1)
		exitcode=$?
		if [ $exitcode -ne 0 ]; then
			echo "$running" >&2
			container_logs
			docker compose $COMPOSE_ARGS down
			echo "An error occured while waiting for $name to be done." >&2
			exit 1
		fi
		if [ "$running" == "true" ]; then
			echo "Waiting for $name to be done ($((VISUALIZATION_MAX_SECONDS-seconds))s remaining)"
			seconds=$((seconds+1))
			sleep 1
		fi
	done
done
echo "Starting test"

docker exec -u `id -u`:`id -g` $TEST_CONTAINER python /work/test.py -v
status=$?

container_logs
docker compose $COMPOSE_ARGS down

# Note the successful build with the environment used to build it
for repo in $VISUALIZATION_NAMES; do
	tree="$PWD/$REPO_ROOT/$repo"
	echo "$VISUALIZATION_ENV" > "$tree/.skip_build"
done

echo "# Let SonarQube know we have Python tests" > lib/test.py
if [ -d "$PWD/$REPO_ROOT/prediction-site" ]; then
	tree="$PWD/$REPO_ROOT/prediction-site"
	grep -E "sonar\.(scm|tests|test|python|javascript|dependencyCheck)[\.=]" sonar-project.properties >> "$tree/sonar-project.properties"
	cp test/junit/TEST-suite.test_prediction_site.*.xml "$tree/test/junit/"
	cp test/coverage/output/*.json "$tree/test/coverage/output/"
	cp test/test.py "$tree/test/"
	grep "test_prediction_site" test/suite/__init__.py > "$tree/test/suite/__init__.py"
	cp test/suite/test_prediction_site.py "$tree/test/suite/"
	echo "# Let SonarQube know we have Python tests" > "$tree/lib/test.py"
fi

if [ -d "$PWD/security" ]; then
	GIT_DIR="$PWD/security/.git" GIT_WORK_TREE="$PWD/security" git checkout -- security_dependencycheck.sh
fi
update_repo "$PWD/security" "https://github.com/ICTU/security-tooling"
sed --in-place="" -e 's/\r$//' ./security/*.sh
cp test/suppression.xml security/suppression.xml
VISUALIZATION_MOUNTS=$(echo $VISUALIZATION_NAMES | sed "s/\\(\\S*\\)/-v $BRANCH_NAME-\\1-modules:\\/src\\/repos\\/\\1\\/node_modules/g")
sed --in-place="" -e "s/\\(:\\/src:z\\)/\\1 \$VISUALIZATION_MOUNTS -v \$SITE_MOUNT:\\/src\\/node_modules/" -e "s/\\(--out \\/report\\)/--exclude \"**\\/public\\/**\" --exclude \"**\\/www\\/**\" --exclude \"**\\/test\\/**\" --exclude \"**\\/security\\/**\" --exclude \"**\\/axe-core\\/**\" --exclude \"**\\/.git\\/**\" --project \"\$PROJECT_NAME\" --disableOssIndex true \\1/" ./security/security_dependencycheck.sh
PROJECT_NAME="Visualizations" VISUALIZATION_MOUNTS="$VISUALIZATION_MOUNTS" SITE_MOUNT="$BRANCH_NAME-visualization-site-modules" bash ./security/security_dependencycheck.sh "$PWD" "$PWD/test/owasp-dep"
if [ -d "$PWD/$REPO_ROOT/prediction-site" ]; then
	tree="$PWD/$REPO_ROOT/prediction-site"
	mkdir -p -m 0777 "$tree/security"
	PROJECT_NAME="Prediction site" VISUALIZATION_MOUNTS="" SITE_MOUNT="$BRANCH_NAME-prediction-site-modules" bash ./security/security_dependencycheck.sh "$tree" "$tree/test/owasp-dep"
fi

if [ $status -ne 0 ]; then
	exit 2
fi

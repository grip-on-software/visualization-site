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
    if [ ! -f "$VISUALIZATION_SITE_CONFIGURATION" ]; then
        VISUALIZATION_SITE_CONFIGURATION="lib/config.json"
    fi
fi

# Comparable integer format for versions - https://stackoverflow.com/a/37939589
function version() {
	echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }';
}

COMPOSE_VERSION=$(docker-compose version --short)
COMPOSE_ARGS="-p ${BUILD_TAG:-visualization} -f caddy/docker-compose.yml"
if [ $(version $COMPOSE_VERSION) -lt $(version "1.7.0") ]; then
	sed -E 's/( +)shm_size: .*/\1volumes:\'$'\n''\1  - \/dev\/shm:\/dev\/shm/' test/docker-compose.yml > test/docker-compose.shm.yml
	COMPOSE_ARGS="$COMPOSE_ARGS -f test/docker-compose.shm.yml"
else
	COMPOSE_ARGS="$COMPOSE_ARGS -f test/docker-compose.yml"
fi

function container_logs() {
	echo '<h2>Docker container logs</h2><ul>' >> test/results/index.html

	docker-compose $COMPOSE_ARGS ps -q | xargs -L 1 -I {} /bin/bash -c '
		docker inspect --format="$(cat log-format.txt)" {} > test/results/logs_{}.html
		echo "<pre>" >> test/results/logs_{}.html
		docker logs {} 2>&1 | sed "s/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g" >> test/results/logs_{}.html 2>&1
		echo "</pre></body></html>" >> test/results/logs_{}.html
		echo "<li><a href=\"logs_{}.html\">$(docker inspect --format={{.Name}} {}) ($(docker logs {} 2>&1 | wc -c) bytes)</a></li>" >> test/results/index.html'

	echo '</ul></body></html>' >> test/results/index.html
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

function update_repo() {
	tree=$1
	shift
	url=$1
	shift
	build_check=$1
	if [ ! -d $tree ]; then
		echo "Cloning $tree"
		git clone $url $tree
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
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git fetch origin master
		LOCAL_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse HEAD)
		REMOTE_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse FETCH_HEAD)
		if [ ! -z "$build_check" ] && [ $LOCAL_REV = $REMOTE_REV ] && [ "$VISUALIZATION_ENV" = "$previous_env" ]; then
			echo "$repo is up to date, skipping build in instance."
			echo "$VISUALIZATION_ENV" > "$tree/.skip_build"
		else
			GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git pull origin master
			if [ ! -z "$build_check" ]; then
				echo "Build of $repo required"
				rm -f "$tree/.skip_build"
				docker ps -q -a --filter "volume=$BRANCH_NAME-$repo-modules" | xargs --no-run-if-empty docker stop
				docker volume rm -f "$BRANCH_NAME-$repo-modules"
			fi
		fi
	fi
}

for repo in $VISUALIZATION_NAMES; do
	tree="$PWD/$REPO_ROOT/$repo"
	url=$(git config --get remote.origin.url | sed s/visualization-site/$repo/)
	update_repo "$tree" "$url" 1
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

PROXY_HOST=nginx

docker-compose $COMPOSE_ARGS pull
docker-compose $COMPOSE_ARGS up -d --force-recreate

TEST_CONTAINER=$(docker-compose $COMPOSE_ARGS ps -q runner)
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
	container=$(docker-compose $COMPOSE_ARGS ps -q $name)
	running="true"
	while [ "$running" == "true" ]; do
		if [ $seconds -gt $VISUALIZATION_MAX_SECONDS ]; then
			container_logs
			docker-compose $COMPOSE_ARGS down
			echo "$name did not seem to be done after ${VISUALIZATION_MAX_SECONDS}s." >&2
			exit 1
		fi

		# Check if the visualization is done building
		running=$(docker inspect -f '{{.State.Running}}' $container 2>&1)
		exitcode=$?
		if [ $exitcode -ne 0 ]; then
			echo "$running" >&2
			container_logs
			docker-compose $COMPOSE_ARGS down
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

docker exec -u `id -u`:`id -g` $TEST_CONTAINER python /work/test.py
status=$?

container_logs
docker-compose $COMPOSE_ARGS down

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
sed --in-place="" -e "s/\\(:\\/src:z\\)/\\1 \$VISUALIZATION_MOUNTS -v \$SITE_MOUNT:\\/src\\/node_modules/" -e "s/\\(--out \\/report\\)/--exclude \"**\\/public\\/**\" --exclude \"**\\/www\\/**\" --exclude \"**\\/test\\/**\" --exclude \"**\\/security\\/**\" --exclude \"**\\/axe-core\\/**\" --exclude \"**\\/.git\\/**\" --project \"\$PROJECT_NAME\" \\1/" ./security/security_dependencycheck.sh
PROJECT_NAME="Visualizations" VISUALIZATION_MOUNTS="$VISUALIZATION_MOUNTS" SITE_MOUNT="$BRANCH_NAME-visualization-site-modules" bash ./security/security_dependencycheck.sh "$PWD" "$PWD/test/owasp-dep"
if [ -d "$PWD/$REPO_ROOT/prediction-site" ]; then
	tree="$PWD/$REPO_ROOT/prediction-site"
	mkdir -p -m 0777 "$tree/security"
	PROJECT_NAME="Prediction site" VISUALIZATION_MOUNTS="" SITE_MOUNT="$BRANCH_NAME-prediction-site-modules" bash ./security/security_dependencycheck.sh "$tree" "$tree/test/owasp-dep"
fi

if [ $status -ne 0 ]; then
	exit 2
fi

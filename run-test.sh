#!/bin/bash

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
	echo '<h1>Logs</h1><ul>' >> test/results/index.html

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
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git reset --hard
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git fetch origin master
		LOCAL_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse HEAD)
		REMOTE_REV=$(GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git rev-parse FETCH_HEAD)
		if [ ! -z "$build_check" ] && [ $LOCAL_REV = $REMOTE_REV ] && [ -f "$tree/public/index.html" ]; then
			echo "$repo is up to date, skipping build in instance."
			touch "$tree/.skip_build"
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
	cmp -s $PREDICTION_CONFIGURATION "$tree/config.json"
	if [ $? -ne 0 ]; then
		echo "Including new configuration file for prediction-site (rebuild)"
		cp -f --no-preserve=mode,ownership $PREDICTION_CONFIGURATION "$tree/config.json"
		rm -f "$tree/.skip_build"
	fi
	rm -rf "$tree/test"
	mkdir -p "$tree/test/junit" "$tree/test/coverage/output" "$tree/test/suite"
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
docker exec $TEST_CONTAINER pip install unittest-xml-reporting selenium axe-selenium-python

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

		# Check if port 3000 is opened by the visualization
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

echo "# Let SonarQube know we have Python tests" > lib/test.py
if [ -d "$PWD/$REPO_ROOT/prediction-site" ]; then
	tree="$PWD/$REPO_ROOT/prediction-site"
	grep -E "sonar\.(tests|test|python|javascript)\." sonar-project.properties >> "$tree/sonar-project.properties"
	cp test/junit/TEST-suite.test_prediction_site.*.xml "$tree/test/junit/"
	cp test/coverage/output/*.json "$tree/test/coverage/output/"
	cp test/test.py "$tree/test/"
	cp test/suite/test_prediction_site.py "$tree/test/suite/"
	echo "# Let SonarQube know we have Python tests" > "$tree/lib/test.py"
fi

if [ -d "$PWD/security" ]; then
	GIT_DIR="$PWD/security/.git" GIT_WORK_TREE="$PWD/security" git checkout -- security_dependencycheck.sh
fi
update_repo "$PWD/security" "https://github.com/ICTU/security-tooling"
sed --in-place="" -e 's/\r$//' ./security/*.sh
cp test/suppression.xml security/suppression.xml
VISUALIZATION_MOUNTS=$(echo $VISUALIZATION_NAMES | sed "s/\\(\\S*\\)/-v $BRANCH_NAME-\\1-modules:\\\\\\/src\\\\\\/repos\\\\\\/\\1\\\\\\/node_modules/g")
sed --in-place="" -e "s/\\(:\\/src:z\\)/\\1 $VISUALIZATION_MOUNTS -v $BRANCH_NAME-visualization-site-modules:\\/src\\/node_modules/" -e "s/\\(--out \\/report\\)/--exclude \"**\\/public\\/**\" --exclude \"**\\/www\\/**\" --exclude \"**\\/test\\/**\" --exclude \"**\\/security\\/**\" --exclude \"**\\/axe-core\\/**\" --exclude \"**\\/.git\\/**\" \\1/" ./security/security_dependencycheck.sh
PROJECT_NAME="Visualizations" bash ./security/security_dependencycheck.sh "$PWD" "$PWD/test/owasp-dep"

if [ $status -ne 0 ]; then
	exit 2
fi

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
		docker logs {} >> test/results/logs_{}.html 2>&1
		echo "</pre></body></html>" >> test/results/logs_{}.html
		echo "<li><a href=\"logs_{}.html\">$(docker inspect --format={{.Name}} {}) ($(docker logs {} 2>&1 | wc -c) bytes)</a></li>" >> test/results/index.html'

	echo '</ul></body></html>' >> test/results/index.html
}

rm -rf test/junit test/results test/coverage
mkdir -p repos
mkdir -p test/junit test/results test/coverage

if [ -z "$REPO_ROOT" ]; then
	REPO_ROOT="repos"
else
	has_repo_root=1
fi

if [ -z "$VISUALIZATION_NAMES" ]; then
	VISUALIZATION_NAMES=$(cat visualization_names.txt)
fi

for repo in $VISUALIZATION_NAMES; do
	tree="$PWD/$REPO_ROOT/$repo"
	if [ ! -d $tree ]; then
		echo "Cloning $tree"
		url=$(git config --get remote.origin.url | sed s/visualization-site/$repo/)
		git clone $url $tree
	elif [ ! -z "$has_repo_root" ]; then
		echo "Keeping $tree intact"
		if [ -d "$tree/node_modules" ]; then
			mv "$tree/node_modules" "$tree/node_modules.bak"
		fi
	else
		echo "Updating $tree"
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git reset --hard
		GIT_DIR="$tree/.git" GIT_WORK_TREE=$tree git pull origin master
	fi
done

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
docker exec $TEST_CONTAINER pip install unittest-xml-reporting selenium

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

if [ $status -ne 0 ]; then
	exit 2
fi

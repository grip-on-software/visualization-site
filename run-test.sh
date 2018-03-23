#!/bin/bash

# Comparable integer format for versions - https://stackoverflow.com/a/37939589
function version() {
	echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }';
}

COMPOSE_VERSION=$(docker-compose version --short)
COMPOSE_FILES="-f caddy/docker-compose.yml"
if [ $(version $COMPOSE_VERSION) -lt $(version "1.7.0") ]; then
	sed -E 's/( +)shm_size: .*/\1volumes:\'$'\n''\1  - \/dev\/shm:\/dev\/shm/' test/docker-compose.yml > test/docker-compose.shm.yml
	COMPOSE_FILES="$COMPOSE_FILES -f test/docker-compose.shm.yml"
else
	COMPOSE_FILES="$COMPOSE_FILES -f test/docker-compose.yml"
fi

PROXY_HOST=nginx

docker-compose $COMPOSE_FILES up -d --force-recreate

TEST_CONTAINER=$(docker-compose $COMPOSE_FILES ps -q test)
if [ -z "$TEST_CONTAINER" ]; then
	docker-compose $COMPOSE_FILES ps -q | xargs -L 1 docker logs
	echo "Could not bring up the test instances."
	exit 1
fi

echo "Up"
docker exec $TEST_CONTAINER pip install unittest-xml-reporting selenium
docker exec $TEST_CONTAINER python /work/test.py
status=$?

if [ $status -ne 0 ]; then
	docker-compose $COMPOSE_FILES ps -q | xargs -L 1 docker logs
fi

docker-compose $COMPOSE_FILES down

exit $status

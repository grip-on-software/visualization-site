#!/bin/bash

pip install selenium

COMPOSE_FILES="-f caddy/docker-compose.yml -f test/docker-compose.yml"
PROXY_HOST=nginx

docker-compose $COMPOSE_FILES up -d

echo "Up"

python test/test.py
status=$?

if [ $status -ne 0 ]; then
	docker-compose $COMPOSE_FILES logs
fi

docker-compose $COMPOSE_FILES down

exit $status

#!/bin/bash

log_path=/var/log/nginx
CONFIG="config.json"
if [ ! -f "$CONFIG" ]; then
    CONFIG="lib/config.json"
fi
params="-o /srv/goaccess-report/analytics/index.html --log-format='%^[%d:%t %^] \"%r\" %s %b \"%R\" \"%u\" ~h{,\" }' --date-format '%d/%b/%Y' --time-format '%H:%M:%S' --all-static-files --static-file .json"
if [ ! -z "$GOACCESS_DAEMON" ]; then
	params="$params --origin=http://$(jq -r .visualization_server) --ws-url=$(jq -r .websocket_server):80 --addr=127.0.0.1 --real-time-html"
fi

zcat $log_path/access.log-*.gz | bash -c "/usr/local/bin/goaccess $params $log_path/access.log -"

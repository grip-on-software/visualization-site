#!/bin/bash
# Start a GoAccess server to display access logs.
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

#!/bin/bash

zcat /var/log/nginx/access.log-*.gz | /usr/local/bin/goaccess -o /srv/goaccess-report/analytics/index.html --log-format='%^[%d:%t %^] "%r" %s %b "%R" "%u" ~h{," }' --date-format '%d/%b/%Y' --time-format '%H:%M:%S' /var/log/nginx/access.log -

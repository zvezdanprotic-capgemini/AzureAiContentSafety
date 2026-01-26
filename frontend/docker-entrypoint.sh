#!/usr/bin/env sh
set -eu

: "${BACKEND_ORIGIN:?BACKEND_ORIGIN is required (e.g. http://backend:8000)}"

envsubst '${BACKEND_ORIGIN}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'

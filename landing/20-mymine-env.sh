#!/bin/sh
set -eu

: "${AUTH_BASE_URL:?AUTH_BASE_URL is required}"
: "${MC_ADDRESS:?MC_ADDRESS is required}"
: "${MC_VERSION:=26.2}"
: "${HMCL_VERSION:=3.16.3}"
: "${MAP_URL:=/map/}"

export AUTH_BASE_URL MC_ADDRESS MC_VERSION HMCL_VERSION MAP_URL
envsubst '${AUTH_BASE_URL} ${MC_ADDRESS} ${MC_VERSION} ${HMCL_VERSION} ${MAP_URL}' \
  < /opt/mymine/index.html.template \
  > /usr/share/nginx/html/index.html

AUTH_URL="${AUTH_BASE_URL%/}/"
printf '{\n  "urls": ["%s"]\n}\n' "$AUTH_URL" \
  > /usr/share/nginx/html/authlib-injectors.json

printf '{"minecraft":"%s","auth":"%s","version":"%s","map":"%s"}\n' \
  "$MC_ADDRESS" "$AUTH_URL" "$MC_VERSION" "$MAP_URL" \
  > /usr/share/nginx/html/server.json

#!/bin/sh
set -eu
. /opt/mymine/server-env.sh
mymine_configure_server
exec /image/scripts/start "$@"

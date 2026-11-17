#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "$(find mods -maxdepth 1 -type f -name '*.jar' 2>/dev/null | wc -l)" -ne 9 ]; then
  echo "Missing original mods: first run python3 build_pack.py" >&2
  exit 1
fi
if [ "${MYMINE_ALLOW_PARALLEL:-0}" != "1" ] &&
   [ "$(docker inspect --format '{{.State.Running}}' mymine 2>/dev/null || true)" = "true" ]; then
  echo "Refusing to start second Minecraft while normal MyMine is running." >&2
  echo "tomas has ~8 GiB RAM. Safely stop normal Minecraft first." >&2
  echo "Existing world, Drasl and landing are not deleted or changed." >&2
  exit 1
fi
docker compose -p mymine-engineering -f compose.yml up -d
docker compose -p mymine-engineering -f compose.yml ps

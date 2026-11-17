#!/bin/sh
set -eu
cd "$(dirname "$0")"
# The standalone test uses the signed/locked GHCR Engineering image.
# Local JARs are needed only when preparing a new release, not to start.
test -f releases/MyMine-Engineering-0.2.0.mrpack || {
  echo "Missing pinned Engineering client profile" >&2
  exit 1
}
if [ "${MYMINE_ALLOW_PARALLEL:-0}" != "1" ] &&
   [ "$(docker inspect --format '{{.State.Running}}' mymine 2>/dev/null || true)" = "true" ]; then
  echo "Refusing to start second Minecraft while normal MyMine is running." >&2
  echo "tomas has ~8 GiB RAM. Safely stop normal Minecraft first." >&2
  echo "Existing world, Drasl and landing are not deleted or changed." >&2
  exit 1
fi
docker compose -p mymine-engineering -f compose.yml up -d
docker compose -p mymine-engineering -f compose.yml ps

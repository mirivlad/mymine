#!/usr/bin/env bash
set -euo pipefail

COMPOSE=(docker compose -f compose.yml -f compose.dev.yml)
CONTAINER=${CONTAINER_NAME:-mymine-test}
TIMEOUT=${SMOKE_TIMEOUT:-300}
MIN_JARS=${MIN_JARS:-17}
MAP_PORT=${MAP_PORT:-8100}
BLUEMAP_ACCEPT_DOWNLOAD=${BLUEMAP_ACCEPT_DOWNLOAD:-false}

"${COMPOSE[@]}" up -d --build --force-recreate minecraft
printf 'Waiting up to %ss for Minecraft healthcheck...\n' "$TIMEOUT"

for ((i=0; i<TIMEOUT; i+=5)); do
  status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CONTAINER" 2>/dev/null || true)
  if [[ "$status" == healthy ]]; then
    jar_count=$(docker exec "$CONTAINER" sh -lc "find /data/mods -maxdepth 1 -type f -name '*.jar' | wc -l")
    loaded=$(docker logs "$CONTAINER" 2>&1 | sed -n 's/.*Loading \([0-9][0-9]*\) mods:.*/\1/p' | tail -1)
    [[ "$jar_count" -ge "$MIN_JARS" ]] || { echo "Only $jar_count mod jars in /data/mods" >&2; exit 1; }
    [[ -n "$loaded" && "$loaded" -gt 4 ]] || { echo "Fabric reports only ${loaded:-0} loaded mods" >&2; exit 1; }

    mod_files=$(docker exec "$CONTAINER" sh -lc "find /data/mods -maxdepth 1 -type f -name '*.jar' -printf '%f\n' | tr '[:upper:]' '[:lower:]'")
    for required in alternate-current graves fallingtree bluemap; do
      grep -q "$required" <<<"$mod_files" || { echo "Required mod missing: $required" >&2; exit 1; }
    done

    docker exec "$CONTAINER" sh -lc "grep -q 'render-thread-count: 1' /data/config/bluemap/core.conf" || { echo 'BlueMap managed config missing' >&2; exit 1; }
    if docker logs "$CONTAINER" 2>&1 | grep -q 'Failed to load bluemap'; then
      echo 'BlueMap reported a load failure' >&2
      docker logs --tail=120 "$CONTAINER" >&2 || true
      exit 1
    fi
    if [[ "$BLUEMAP_ACCEPT_DOWNLOAD" == true ]]; then
      bluemap_ready=false
      for ((j=0; j<60; j+=2)); do
        if curl -fsS --max-time 2 "http://127.0.0.1:${MAP_PORT}/" >/dev/null 2>&1; then
          bluemap_ready=true
          break
        fi
        if docker logs "$CONTAINER" 2>&1 | grep -q 'Failed to load bluemap'; then
          break
        fi
        sleep 2
      done
      [[ "$bluemap_ready" == true ]] || { echo "BlueMap web endpoint not ready on port $MAP_PORT" >&2; docker logs --tail=120 "$CONTAINER" >&2 || true; exit 1; }
      bluemap_state='HTTP ready'
    else
      docker logs "$CONTAINER" 2>&1 | grep -q 'You must accept the required file download' || { echo 'BlueMap did not report expected download opt-in state' >&2; exit 1; }
      bluemap_state='waiting for explicit resource-download opt-in'
    fi
    docker exec "$CONTAINER" mc-health >/dev/null
    echo "Minecraft healthy; jars=$jar_count, Fabric loaded=$loaded mods; BlueMap $bluemap_state."
    docker ps --filter "name=^/${CONTAINER}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    exit 0
  fi
  if [[ "$status" == unhealthy ]]; then
    echo 'Minecraft became unhealthy.' >&2
    docker logs --tail=200 "$CONTAINER" >&2 || true
    exit 1
  fi
  sleep 5
done

echo 'Timed out waiting for Minecraft.' >&2
docker logs --tail=200 "$CONTAINER" >&2 || true
exit 1

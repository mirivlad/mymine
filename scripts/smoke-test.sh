#!/usr/bin/env bash
set -euo pipefail

COMPOSE=(docker compose -f compose.yml -f compose.dev.yml)
CONTAINER=${CONTAINER_NAME:-mymine-test}
TIMEOUT=${SMOKE_TIMEOUT:-300}
MIN_JARS=${MIN_JARS:-13}

"${COMPOSE[@]}" up -d --build minecraft
printf 'Waiting up to %ss for Minecraft healthcheck...\n' "$TIMEOUT"

for ((i=0; i<TIMEOUT; i+=5)); do
  status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CONTAINER" 2>/dev/null || true)
  if [[ "$status" == healthy ]]; then
    jar_count=$(docker exec "$CONTAINER" sh -lc "find /data/mods -maxdepth 1 -type f -name '*.jar' | wc -l")
    loaded=$(docker logs "$CONTAINER" 2>&1 | sed -n 's/.*Loading \([0-9][0-9]*\) mods:.*/\1/p' | tail -1)
    [[ "$jar_count" -ge "$MIN_JARS" ]] || { echo "Only $jar_count mod jars in /data/mods" >&2; exit 1; }
    [[ -n "$loaded" && "$loaded" -gt 4 ]] || { echo "Fabric reports only ${loaded:-0} loaded mods" >&2; exit 1; }
    docker exec "$CONTAINER" mc-health >/dev/null
    echo "Minecraft healthy; jars=$jar_count, Fabric loaded=$loaded mods."
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

#!/bin/sh
set -eu
# The Minecraft version is determined by the image, not Portainer variables.
VERSION=$(tr -d '\r\n' </opt/mymine/minecraft-version.txt)
case "$VERSION" in
  ''|*[!0-9a-zA-Z._+-]*) echo "MyMine: invalid baked Minecraft version" >&2; exit 1 ;;
esac
export VERSION
# Migrate old generated MOTD values which embedded a now-stale version.
case "$(printenv MOTD 2>/dev/null || true)" in
  "MyMine — Minecraft "*|"MyMine — Fabric "*)
    MOTD="MyMine — мир приключений"
    export MOTD ;;
esac
printf 'MyMine: starting Minecraft %s (from image metadata)\n' "$VERSION"
exec /image/scripts/start "$@"

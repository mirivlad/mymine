#!/bin/sh
set -eu
# The game may still be loading; the worker retries without blocking nginx.
python3 /opt/mymine/minecraft-status.py --interval 45 &
printf 'MyMine landing: live Minecraft status watcher started (PID %s)\n' "$!"

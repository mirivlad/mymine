#!/bin/sh
set -eu
. /opt/mymine/server-env.sh
mymine_configure_server
# Engineering uses a per-world NeoForge server config. Keep the source of truth
# in Portainer environment variables. This changes sky time only, NOT tick rate.
if [ "${MYMINE_EDITION:-classic}" = engineering ]; then
    day="${MYMINE_DAY_MINUTES:-20}"
    night="${MYMINE_NIGHT_MINUTES:-10}"
    for value in "$day" "$night"; do
        case "$value" in
            ""|*[!0-9]*) echo "MyMine: day/night minutes must be positive integers" >&2; exit 1 ;;
        esac
        [ "$value" -ge 1 ] && [ "$value" -le 1440 ] || {
            echo "MyMine: day/night must be between 1 and 1440 minutes" >&2; exit 1;
        }
    done
    world="${LEVEL:-world}"
    case "$world" in *..*|*/*|"") echo "MyMine: unsafe world name for time config" >&2; exit 1;; esac
    config_dir="/data/$world/serverconfig"
    mkdir -p "$config_dir"
    target="$config_dir/timecontrol-server.toml"
    tmp="$target.tmp.$$"
    trap 'rm -f "$tmp"' EXIT HUP INT TERM
    cat > "$tmp" <<EOF
[system_time]
    sync_to_system_time = false
    sync_to_system_time_rate = 20
[arbitrary_time]
    day_length_minutes = $day
    night_length_minutes = $night
[miscellaneous]
    debug = false
EOF
    mv "$tmp" "$target"
    trap - EXIT HUP INT TERM
    printf 'MyMine Engineering time: day=%s min, night=%s min\n' "$day" "$night"
fi
exec /image/scripts/start "$@"

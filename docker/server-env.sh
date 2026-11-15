#!/bin/sh
# Called by the image entrypoint; sourceable independently by tests.
mymine_configure_server() {
    # The bundled version is authoritative; inherited VERSION=LATEST/26.2 is not.
    VERSION=$(tr -d '\r\n' </opt/mymine/minecraft-version.txt)
    case "$VERSION" in
        ''|*[!0-9a-zA-Z._+-]*)
            echo "MyMine: invalid Minecraft version embedded in the image" >&2
            return 1 ;;
    esac
    export VERSION

    # Preserve a custom MOTD, but always render the actual server version.
    # Legacy generated messages with an outdated version are repaired.
    case "${MOTD-}" in
        ""|"MyMine — Minecraft "*|"MyMine — Fabric "*)
            MOTD="MyMine — Minecraft $VERSION" ;;
        *'{version}'*)
            MOTD=$(printf '%s' "$MOTD" | sed "s/{version}/$VERSION/g") ;;
        *"Minecraft "[0-9]*)
            MOTD=$(printf '%s' "$MOTD" | sed -E "s/Minecraft [0-9][0-9A-Za-z._+-]*$/Minecraft $VERSION/") ;;
        *)
            MOTD="$MOTD · Minecraft $VERSION" ;;
    esac
    export MOTD
    printf 'MyMine: Minecraft %s; MOTD: %s\n' "$VERSION" "$MOTD"
}

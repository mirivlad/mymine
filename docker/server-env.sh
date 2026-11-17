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

    MYMINE_EDITION=${MYMINE_EDITION:-classic}
    case "$MYMINE_EDITION" in
      classic|engineering) ;;
      *) echo "Invalid MYMINE_EDITION=$MYMINE_EDITION (use classic or engineering)" >&2; return 1 ;;
    esac
    MYMINE_BAKED_EDITION=${MYMINE_BAKED_EDITION:-classic}
    if [ "$MYMINE_EDITION" != "$MYMINE_BAKED_EDITION" ]; then
        echo "Wrong server image: selected $MYMINE_EDITION, image contains $MYMINE_BAKED_EDITION" >&2
        return 1
    fi

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
    if [ "$MYMINE_EDITION" = engineering ]; then
        # Old classic Portainer defaults must not follow into the new world.
        case "$MOTD" in
          "MyMine — Minecraft "*|"MyMine — мир приключений"*|"MyMine — Fabric "*)
            MOTD="MyMine Engineering — Minecraft $VERSION" ;;
          *"Engineering"*) ;;
          *) MOTD="MyMine Engineering — Minecraft $VERSION" ;;
        esac
    fi
    export MOTD
    printf 'MyMine [%s]: Minecraft %s; MOTD: %s\n' "$MYMINE_EDITION" "$VERSION" "$MOTD"
}

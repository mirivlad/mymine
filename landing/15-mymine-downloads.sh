#!/bin/sh
set -eu

: "${AUTH_BASE_URL:?AUTH_BASE_URL is required}"
: "${MC_ADDRESS:?MC_ADDRESS is required}"
: "${HMCL_VERSION:=3.16.3}"
: "${SERVER_NAME:=MyMine}"

DOWNLOAD_DIR=/usr/share/nginx/html/downloads
AUTH_URL="${AUTH_BASE_URL%/}/"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT INT TERM

cat > "$TMP/mymine-instance.properties" <<EOF_CONFIG
auth.url=$AUTH_URL
server.name=$SERVER_NAME
server.address=$MC_ADDRESS
EOF_CONFIG

patch_zip_artifact() {
    artifact=$1
    test -f "$artifact"
    /opt/mymine/patch-launcher.py "$artifact" "$TMP/mymine-instance.properties"
}

for ext in exe jar sh; do
    patch_zip_artifact "$DOWNLOAD_DIR/MyMineLauncher-${HMCL_VERSION}.${ext}"
done

DEB="$DOWNLOAD_DIR/MyMineLauncher-${HMCL_VERSION}.deb"
DEB_ROOT="$TMP/deb-root"
dpkg-deb -R "$DEB" "$DEB_ROOT"
DEB_PAYLOAD="$DEB_ROOT/usr/share/java/mymine-launcher/MyMineLauncher-${HMCL_VERSION}.sh"
if [ ! -f "$DEB_PAYLOAD" ]; then
    # Compatibility with pre-rebrand launcher artifacts while rolling upgrades.
    DEB_PAYLOAD="$DEB_ROOT/usr/share/java/hmcl/HMCL-${HMCL_VERSION}.sh"
fi
patch_zip_artifact "$DEB_PAYLOAD"
dpkg-deb -b "$DEB_ROOT" "$TMP/launcher.deb" >/dev/null
mv "$TMP/launcher.deb" "$DEB"

(
    cd "$DOWNLOAD_DIR"
    sha256sum \
        "MyMineLauncher-${HMCL_VERSION}.exe" \
        "MyMineLauncher-${HMCL_VERSION}.jar" \
        "MyMineLauncher-${HMCL_VERSION}.deb" \
        "MyMineLauncher-${HMCL_VERSION}.sh" \
        "MyMineLauncher-${HMCL_VERSION}-source.tar.gz" \
        > SHA256SUMS
)

printf 'Prepared MyMine Launcher downloads for auth %s and server %s (%s)\n' \
    "$AUTH_URL" "$SERVER_NAME" "$MC_ADDRESS"

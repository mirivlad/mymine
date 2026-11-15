#!/bin/sh
# Resolve the launcher version from this image's bundled artifacts. Never trust
# an inherited HMCL_VERSION from Portainer or another deployment environment.
resolve_mymine_launcher_version() {
    _mymine_download_dir=${DOWNLOAD_DIR:-/usr/share/nginx/html/downloads}
    set -- "$_mymine_download_dir"/MyMineLauncher-*.jar

    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
        printf '%s\n' "MyMine landing: expected exactly one MyMineLauncher-*.jar in $_mymine_download_dir (found $# candidates)" >&2
        return 1
    fi

    _mymine_name=${1##*/}
    HMCL_VERSION=${_mymine_name#MyMineLauncher-}
    HMCL_VERSION=${HMCL_VERSION%.jar}
    case "$HMCL_VERSION" in
        ""|*[!a-zA-Z0-9.+_-]*)
            printf 'MyMine landing: invalid launcher version: %s\n' "$HMCL_VERSION" >&2
            return 1
            ;;
    esac

    for _mymine_suffix in .exe .sh .deb -source.tar.gz; do
        if [ ! -s "$_mymine_download_dir/MyMineLauncher-$HMCL_VERSION$_mymine_suffix" ]; then
            printf 'MyMine landing: missing launcher artifact: MyMineLauncher-%s%s\n' "$HMCL_VERSION" "$_mymine_suffix" >&2
            return 1
        fi
    done
    export HMCL_VERSION
    printf 'MyMine landing: detected launcher version %s from bundled files\n' "$HMCL_VERSION"
}

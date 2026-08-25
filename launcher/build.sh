#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HMCL_VERSION=${HMCL_VERSION:-3.16.3}
MYMINE_AUTH_URL=${MYMINE_AUTH_URL:-https://auth.mymine.mirv.top/}
MYMINE_SERVER_NAME=${MYMINE_SERVER_NAME:-MyMine}
MYMINE_SERVER_ADDRESS=${MYMINE_SERVER_ADDRESS:-mymine.mirv.top:25565}
WORKDIR=${WORKDIR:-$ROOT/.build/hmcl}
DIST_DIR=${DIST_DIR:-$ROOT/landing/downloads}
VERSION_ROOT=${HMCL_VERSION%.*}
BUILD_NUMBER=${HMCL_VERSION##*.}

rm -rf "$WORKDIR"
mkdir -p "$(dirname "$WORKDIR")" "$DIST_DIR"
find "$DIST_DIR" -mindepth 1 ! -name .gitkeep -delete

git clone --depth 1 --branch "v${HMCL_VERSION}" \
  https://github.com/HMCL-dev/HMCL.git "$WORKDIR"

MYMINE_AUTH_URL="$MYMINE_AUTH_URL" \
MYMINE_SERVER_NAME="$MYMINE_SERVER_NAME" \
MYMINE_SERVER_ADDRESS="$MYMINE_SERVER_ADDRESS" \
  python3 "$ROOT/launcher/patch-hmcl.py" "$WORKDIR"

(
  cd "$WORKDIR"
  git diff --check
  VERSION_TYPE=stable \
  VERSION_ROOT="$VERSION_ROOT" \
  BUILD_NUMBER="$BUILD_NUMBER" \
    ./gradlew clean build --no-daemon
)

for ext in exe jar deb sh; do
  src=$(find "$WORKDIR/HMCL/build/libs" -maxdepth 1 -type f \
    -name "HMCL-${HMCL_VERSION}.${ext}" -print -quit)
  if [[ -z "$src" ]]; then
    echo "Missing HMCL ${ext} artifact" >&2
    find "$WORKDIR/HMCL/build/libs" -maxdepth 1 -type f -printf '%f\n' | sort >&2
    exit 1
  fi
  cp "$src" "$DIST_DIR/MyMineLauncher-${HMCL_VERSION}.${ext}"
done

tar \
  --exclude=.git \
  --exclude=.gradle \
  --exclude='*/build' \
  --exclude='*/build/*' \
  -C "$WORKDIR" -czf \
  "$DIST_DIR/MyMineLauncher-${HMCL_VERSION}-source.tar.gz" .

(
  cd "$DIST_DIR"
  sha256sum \
    MyMineLauncher-${HMCL_VERSION}.exe \
    MyMineLauncher-${HMCL_VERSION}.jar \
    MyMineLauncher-${HMCL_VERSION}.deb \
    MyMineLauncher-${HMCL_VERSION}.sh \
    MyMineLauncher-${HMCL_VERSION}-source.tar.gz \
    > SHA256SUMS
)

printf 'Built MyMine Launcher %s with auth %s and server %s (%s)\n' \
  "$HMCL_VERSION" "$MYMINE_AUTH_URL" "$MYMINE_SERVER_NAME" "$MYMINE_SERVER_ADDRESS"
ls -lh "$DIST_DIR"

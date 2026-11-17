#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HMCL_VERSION=${HMCL_VERSION:-3.16.4}
MYMINE_AUTH_URL=${MYMINE_AUTH_URL:-https://auth.mymine.mirv.top/}
MYMINE_SERVER_NAME=${MYMINE_SERVER_NAME:-MyMine}
MYMINE_SERVER_ADDRESS=${MYMINE_SERVER_ADDRESS:-mymine.mirv.top:25565}
MYMINE_EDITION=${MYMINE_EDITION:-classic}
WORKDIR=${WORKDIR:-$ROOT/.build/hmcl}
DIST_DIR=${DIST_DIR:-$ROOT/landing/downloads}
VERSION_ROOT=${HMCL_VERSION%.*}
BUILD_NUMBER=${HMCL_VERSION##*.}

rm -rf "$WORKDIR"
mkdir -p "$(dirname "$WORKDIR")" "$DIST_DIR"
find "$DIST_DIR" -mindepth 1 ! -name .gitkeep -delete

git clone --depth 1 --branch "v${HMCL_VERSION}" \
  https://github.com/HMCL-dev/HMCL.git "$WORKDIR"

python3 "$ROOT/launcher/build-client-pack.py" \
  --manifest "$WORKDIR/HMCL/src/main/resources/mymine-client-files.tsv" \
  --mrpack "$DIST_DIR/MyMine-26.3.mrpack"

# One embedded, checksum-verified Engineering profile; never distribute mod JARs.
cp "$ROOT/engineering/releases/MyMine-Engineering-0.2.0.mrpack" "$WORKDIR/HMCL/src/main/resources/mymine-engineering.mrpack"
cp "$ROOT/engineering/releases/MyMine-Engineering-0.2.0.mrpack" "$DIST_DIR/MyMine-Engineering-0.2.0.mrpack"

MYMINE_AUTH_URL="$MYMINE_AUTH_URL" \
MYMINE_SERVER_NAME="$MYMINE_SERVER_NAME" \
MYMINE_EDITION="$MYMINE_EDITION" \
MYMINE_SERVER_ADDRESS="$MYMINE_SERVER_ADDRESS" \
  python3 "$ROOT/launcher/patch-hmcl.py" "$WORKDIR"

(
  cd "$WORKDIR"
  git diff --check
  if command -v javac >/dev/null 2>&1; then
    VERSION_TYPE=stable \
    VERSION_ROOT="$VERSION_ROOT" \
    BUILD_NUMBER="$BUILD_NUMBER" \
      ./gradlew clean build --no-daemon
  else
    # Some hosts have only a JRE. Reuse the same JDK as our GitHub Actions.
    command -v docker >/dev/null 2>&1 || {
      echo "MyMine launcher build requires JDK 25 (javac) or Docker" >&2
      exit 1
    }
    docker run --rm \
      --user "$(id -u):$(id -g)" \
      -v "$WORKDIR:/workspace" -w /workspace \
      -e "HOME=/workspace" -e "GRADLE_USER_HOME=/workspace/.gradle" \
      -e "VERSION_TYPE=stable" -e "VERSION_ROOT=$VERSION_ROOT" \
      -e "BUILD_NUMBER=$BUILD_NUMBER" \
      eclipse-temurin:25-jdk ./gradlew clean build --no-daemon
  fi
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

rebrand_deb() {
  local deb="$DIST_DIR/MyMineLauncher-${HMCL_VERSION}.deb"
  local tmp
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' RETURN

  dpkg-deb -R "$deb" "$tmp/root"

  local old_payload="$tmp/root/usr/share/java/hmcl/HMCL-${HMCL_VERSION}.sh"
  local new_dir="$tmp/root/usr/share/java/mymine-launcher"
  local new_payload="$new_dir/MyMineLauncher-${HMCL_VERSION}.sh"
  test -f "$old_payload"
  mkdir -p "$new_dir"
  mv "$old_payload" "$new_payload"
  rm -rf "$tmp/root/usr/share/java/hmcl"

  rm -f "$tmp/root/usr/bin/hmcl-stable"
  cat > "$tmp/root/usr/bin/mymine-launcher" <<EOF
#!/usr/bin/env bash
set -e
cd "\$HOME"
if [ -z "\${HMCL_USER_HOME:-}" ]; then
    if [ -z "\${XDG_DATA_HOME:-}" ]; then
        base="\$HOME/.local/share"
    else
        base="\$XDG_DATA_HOME"
    fi
    # Preserve settings from MyMine <= 0.4.0, whose upstream Debian package
    # stored data under the HMCL directory.
    if [ -d "\$base/hmcl" ] && [ ! -e "\$base/mymine-launcher" ]; then
        export HMCL_USER_HOME="\$base/hmcl"
    else
        export HMCL_USER_HOME="\$base/mymine-launcher"
    fi
fi
if [ -z "\${HMCL_LOCAL_HOME:-}" ]; then
    export HMCL_LOCAL_HOME="\$HMCL_USER_HOME/local-stable"
fi
if [ -z "\${HMCL_DEPENDENCIES_DIR:-}" ]; then
    export HMCL_DEPENDENCIES_DIR="\$HMCL_USER_HOME/dependencies"
fi
exec /usr/share/java/mymine-launcher/MyMineLauncher-${HMCL_VERSION}.sh "\$@"
EOF
  chmod 0755 "$tmp/root/usr/bin/mymine-launcher" "$new_payload"

  rm -f "$tmp/root/usr/share/applications/hmcl-stable.desktop"
  cat > "$tmp/root/usr/share/applications/mymine-launcher.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=MyMine Launcher
Comment=Minecraft launcher for MyMine
Exec=/usr/bin/mymine-launcher
Icon=mymine-launcher
Terminal=false
StartupNotify=false
Categories=Game;
Keywords=mc;minecraft;mymine;
EOF

  local old_icon="$tmp/root/usr/share/icons/hicolor/256x256/apps/hmcl-stable.png"
  local new_icon="$tmp/root/usr/share/icons/hicolor/256x256/apps/mymine-launcher.png"
  if [ -f "$old_icon" ]; then
    mv "$old_icon" "$new_icon"
  fi

  rm -f "$tmp/root/DEBIAN/postinst" "$tmp/root/DEBIAN/prerm"
  cat > "$tmp/root/DEBIAN/control" <<EOF
Package: mymine-launcher
Version: ${HMCL_VERSION}
Section: games
Priority: optional
Architecture: all
Maintainer: MyMine Project <mirivlad@users.noreply.github.com>
Provides: hmcl
Conflicts: hmcl
Replaces: hmcl
Description: MyMine Launcher
 Preconfigured Minecraft launcher for a MyMine server installation.
 Based on Hello Minecraft! Launcher (HMCL) and distributed under GPLv3.
Homepage: https://github.com/mirivlad/mymine
EOF

  dpkg-deb --build --root-owner-group "$tmp/root" "$deb.new" >/dev/null
  mv "$deb.new" "$deb"
  trap - RETURN
  rm -rf "$tmp"
}

rebrand_deb

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
    MyMine-26.3.mrpack \
    MyMine-Engineering-0.2.0.mrpack \
    > SHA256SUMS
)

printf 'Built MyMine Launcher %s with auth %s and server %s (%s)\n' \
  "$HMCL_VERSION" "$MYMINE_AUTH_URL" "$MYMINE_SERVER_NAME" "$MYMINE_SERVER_ADDRESS"
ls -lh "$DIST_DIR"

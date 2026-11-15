ARG BASE_IMAGE=itzg/minecraft-server:java25@sha256:9d2707c109da523f5f71c2ad7e38e4fdf7e500f8301ea45bc22708036cf593bb
FROM ${BASE_IMAGE}

USER root
ARG MOD_LOADER=fabric

COPY minecraft-version.txt /opt/mymine/minecraft-version.txt
COPY modrinth-mods.txt /tmp/mymine-modrinth-mods.txt
RUN set -eux; \
    mkdir -p /opt/mymine/mods /opt/mymine/config; \
    MC_VERSION="$(cat /opt/mymine/minecraft-version.txt)"; \
    test -n "$MC_VERSION"; \
    mc-image-helper modrinth \
      --game-version="${MC_VERSION}" \
      --loader="${MOD_LOADER}" \
      --projects=@/tmp/mymine-modrinth-mods.txt \
      --download-dependencies=REQUIRED \
      --output-directory=/opt/mymine; \
    find /opt/mymine/mods -maxdepth 1 -type f -name "*.jar" -print0 \
      | sort -z | xargs -0 sha512sum > /opt/mymine/mods.sha512; \
    rm -f /tmp/mymine-modrinth-mods.txt

# Keep entrypoint script changes from invalidating cached mod downloads.
COPY docker/server-entrypoint.sh /opt/mymine/server-entrypoint.sh
COPY docker/server-env.sh /opt/mymine/server-env.sh
RUN chmod +x /opt/mymine/server-entrypoint.sh

ENV TYPE=FABRIC \
    FABRIC_LOADER_VERSION=0.20.1 \
    FABRIC_LAUNCHER_VERSION=1.1.2 \
    COPY_MODS_SRC=/opt/mymine/mods \
    COPY_CONFIG_SRC=/opt/mymine/config \
    REMOVE_OLD_MODS=TRUE \
    REMOVE_OLD_MODS_DEPTH=1 \
    SYNC_SKIP_NEWER_IN_DESTINATION=false \
    REPLACE_ENV_DURING_SYNC=true

LABEL org.opencontainers.image.title="MyMine" \
      org.opencontainers.image.description="Reproducible Fabric Minecraft server distribution" \
      org.opencontainers.image.source="https://github.com/mirivlad/mymine"

ENTRYPOINT ["/opt/mymine/server-entrypoint.sh"]

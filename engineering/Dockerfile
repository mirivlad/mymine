# Engineering image: official mod files are fetched and SHA-512 verified at build.
# Only the pinned URLs in mods.lock.json are used. No third-party JARs are
# checked into this repository or published as independent downloads.
FROM python:3.12-alpine AS mods
COPY engineering/mods.lock.json /tmp/mymine/mods.lock.json
COPY engineering/download_locked_mods.py /tmp/mymine/download_locked_mods.py
RUN python3 /tmp/mymine/download_locked_mods.py /tmp/mymine/mods.lock.json /out/mods

FROM itzg/minecraft-server:java21@sha256:ad1c2569ab3a4e6f032cb04e528455f8a2130196f82b2b37d5842abe032fda2e
USER root
COPY --from=mods /out/mods/ /opt/mymine/mods/
COPY engineering/minecraft-version.txt /opt/mymine/minecraft-version.txt
COPY docker/server-entrypoint.sh /opt/mymine/server-entrypoint.sh
COPY docker/server-env.sh /opt/mymine/server-env.sh
RUN chmod +x /opt/mymine/server-entrypoint.sh && \
    test "$(find /opt/mymine/mods -type f -name '*.jar' | wc -l)" -eq 12
ENV MYMINE_BAKED_EDITION=engineering \
    TYPE=NEOFORGE \
    NEOFORGE_VERSION=21.1.265 \
    COPY_MODS_SRC=/opt/mymine/mods \
    REMOVE_OLD_MODS=TRUE \
    REMOVE_OLD_MODS_DEPTH=1
LABEL org.opencontainers.image.title="MyMine Engineering" \
      org.opencontainers.image.description="NeoForge 1.21.1 + Create Aeronautics + MineColonies" \
      org.opencontainers.image.source="https://github.com/mirivlad/mymine"
ENTRYPOINT ["/opt/mymine/server-entrypoint.sh"]

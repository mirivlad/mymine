FROM nginx:1.29-alpine@sha256:5616878291a2eed594aee8db4dade5878cf7edcb475e59193904b198d9b830de

RUN apk add --no-cache dpkg python3 zstd

COPY minecraft-version.txt /opt/mymine/minecraft-version.txt
COPY landing/templates/ /opt/mymine/templates/
COPY landing/assets/ /usr/share/nginx/html/assets/
COPY landing/patch-launcher.py /opt/mymine/patch-launcher.py
COPY landing/launcher-version.sh /opt/mymine/launcher-version.sh
COPY landing/15-mymine-downloads.sh /docker-entrypoint.d/15-mymine-downloads.sh
COPY landing/20-mymine-env.sh /docker-entrypoint.d/20-mymine-env.sh
COPY landing/minecraft-status.py /opt/mymine/minecraft-status.py
COPY landing/30-mymine-status.sh /docker-entrypoint.d/30-mymine-status.sh
COPY landing/downloads/ /usr/share/nginx/html/downloads/
RUN chmod +x /opt/mymine/patch-launcher.py /docker-entrypoint.d/15-mymine-downloads.sh /docker-entrypoint.d/20-mymine-env.sh /docker-entrypoint.d/30-mymine-status.sh

LABEL org.opencontainers.image.title="MyMine Landing" \
      org.opencontainers.image.description="MyMine server landing and launcher downloads" \
      org.opencontainers.image.source="https://github.com/mirivlad/mymine"

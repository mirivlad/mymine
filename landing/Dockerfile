FROM nginx:1.29-alpine@sha256:5616878291a2eed594aee8db4dade5878cf7edcb475e59193904b198d9b830de

RUN apk add --no-cache dpkg python3

COPY index.html.template /opt/mymine/index.html.template
COPY patch-launcher.py /opt/mymine/patch-launcher.py
COPY 15-mymine-downloads.sh /docker-entrypoint.d/15-mymine-downloads.sh
COPY 20-mymine-env.sh /docker-entrypoint.d/20-mymine-env.sh
COPY downloads/ /usr/share/nginx/html/downloads/
RUN chmod +x /opt/mymine/patch-launcher.py /docker-entrypoint.d/15-mymine-downloads.sh /docker-entrypoint.d/20-mymine-env.sh

LABEL org.opencontainers.image.title="MyMine Landing" \
      org.opencontainers.image.description="MyMine server landing and launcher downloads" \
      org.opencontainers.image.source="https://github.com/mirivlad/mymine"

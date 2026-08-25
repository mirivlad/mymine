FROM nginx:1.29-alpine@sha256:5616878291a2eed594aee8db4dade5878cf7edcb475e59193904b198d9b830de

COPY index.html.template /opt/mymine/index.html.template
COPY 20-mymine-env.sh /docker-entrypoint.d/20-mymine-env.sh
RUN chmod +x /docker-entrypoint.d/20-mymine-env.sh

LABEL org.opencontainers.image.title="MyMine Landing" \
      org.opencontainers.image.description="MyMine server landing and launcher bootstrap" \
      org.opencontainers.image.source="https://github.com/mirivlad/mymine"

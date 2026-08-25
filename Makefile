COMPOSE=docker compose -f compose.yml -f compose.dev.yml

.PHONY: build up down logs ps smoke mods

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200 minecraft

ps:
	$(COMPOSE) ps

smoke:
	./scripts/smoke-test.sh

mods:
	docker run --rm --entrypoint sh mymine:test -lc 'cat /opt/mymine/mods.sha512; echo; find /opt/mymine/mods -maxdepth 1 -type f -name "*.jar" -printf "%f\\n" | sort'

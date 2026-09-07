# MyMine

MyMine — воспроизводимый Docker-стек для собственного Minecraft Java сервера: Fabric-сервер с server-side модами, self-hosted авторизация Drasl, web-регистрация, BlueMap и готовая сборка HMCL для игроков.

Цель проекта — дать администратору цельный серверный комплект, который можно развернуть через Docker Compose / Portainer, а игрокам оставить обычный Minecraft-клиент без ручной установки Fabric и modpack.

## Что входит в стек

- **Minecraft Java 26.2 / Fabric** — игровой сервер;
- **Drasl** — self-hosted Yggdrasil/authlib-совместимая система аккаунтов;
- **MyMine Landing** — лендинг, регистрация, инструкции и раздача лаунчера;
- **BlueMap** — браузерная 3D-карта мира;
- **MyMine Launcher** — воспроизводимая сборка HMCL с преднастроенным MyMine auth;
- **server-side modpack** — расширенная генерация, структуры, survival/QoL и оптимизации без обязательных клиентских модов;
- **GitHub Actions** — CI, сборка launcher/server/landing и release assets.

```text
Internet
   |
   +-- 80/443 --> nginx
   |                +-- mymine.example.org ------> landing:80
   |                +-- mymine.example.org/map/ -> BlueMap:8100
   |                +-- auth.mymine.example.org -> Drasl:25585
   |
   +-- 25565 -------------------------------> Minecraft:25565
                                                    |
                                                    +--> Drasl session API
```

## Политика регистрации и проверка владения Minecraft

MyMine поддерживает два режима через одну переменную:

```dotenv
VERIFY_MINECRAFT_OWNERSHIP=true
```

### `true` — режим по умолчанию

Новая регистрация требует подтвердить владение **существующим Minecraft-профилем**. Drasl импортирует профиль через Mojang API и использует временный **skin challenge** для доказательства контроля над ним.

После регистрации игрок использует отдельный аккаунт MyMine/Drasl; постоянная Microsoft-авторизация при каждом запуске MyMine Launcher не требуется.

Этот режим выбран по умолчанию для публичных установок.

### `false` — независимая регистрация

```dotenv
VERIFY_MINECRAFT_OWNERSHIP=false
```

Drasl разрешает создание самостоятельного MyMine-профиля без автоматической проверки существующего Minecraft-профиля. Это может быть полезно для автономных/закрытых сетей, recovery-сценариев и инфраструктуры, где сервисы Microsoft/Mojang недоступны.

**Важно:** этот режим не является заявлением о праве использовать Minecraft без действующей лицензии и не позиционируется как способ обхода покупки игры. При отключённой проверке MyMine не определяет наличие приобретённой копии; оператор конкретного сервера самостоятельно определяет политику доступа и отвечает за соблюдение применимых Minecraft EULA / Usage Guidelines и других требований.

Переменная `DRASL_REQUIRE_INVITE=true` может дополнительно ограничить любой из двух режимов приглашениями.

Переключение режима регистрации не удаляет уже существующие аккаунты Drasl; оно меняет правила создания/импорта новых профилей.

## Клиент игрока

Для текущей сборки нужен **Minecraft Java 26.2**.

**Fabric, Forge, NeoForge и клиентские моды устанавливать не нужно.** Сервер работает на Fabric, но базовый набор MyMine подобран как server-side и допускает подключение vanilla-клиента той же версии.

Порядок входа:

1. Зарегистрироваться на Drasl/MyMine в соответствии с выбранной администратором политикой.
2. Скачать MyMine Launcher с лендинга.
3. Добавить аккаунт **MyMine**.
4. Установить обычный Minecraft Java 26.2 без mod loader.
5. Запустить игру и открыть «Сетевая игра» — адрес MyMine добавляется лаунчером в список один раз.

## MyMine Launcher

Лаунчер собирается из HMCL 3.16.3 во время CI. Патч воспроизводим и хранится в `launcher/patch-hmcl.py`.

Изменения MyMine:

- внешний Yggdrasil URL встраивается на этапе сборки;
- MyMine становится основным внешним способом входа;
- Microsoft скрыт из списка добавления аккаунта **после того, как отдельная регистрация Drasl уже выполнена**;
- LittleSkin не добавляется новым профилям и удаляется из старых списков;
- ограничение HMCL, требующее Microsoft-аккаунт перед external/offline login, отключено;
- обычный offline-аккаунт HMCL остаётся доступен как локальный режим;
- при первом запуске конкретной установки Minecraft сервер MyMine добавляется первым в `servers.dat`;
- существующие серверы сохраняются, адрес не дублируется;
- миграция выполняется один раз: если игрок позже удалит MyMine из списка, лаунчер не добавит его снова принудительно.

Имя и адрес встроенного сервера задаются при сборке:

```text
MYMINE_SERVER_NAME
MYMINE_SERVER_ADDRESS
MYMINE_AUTH_URL
```

Release публикует:

```text
MyMineLauncher-3.16.3.exe
MyMineLauncher-3.16.3.deb
MyMineLauncher-3.16.3.jar
MyMineLauncher-3.16.3.sh
MyMineLauncher-3.16.3-source.tar.gz
SHA256SUMS
```

Модифицированное дерево исходников HMCL публикуется вместе с бинарниками в соответствии с GPLv3.

## Серверные моды

Прямые версии закреплены в `modrinth-mods.txt`; обязательные зависимости разрешаются при сборке image через Modrinth.

Основные группы:

- **структуры:** Moog's Voyager Structures (MVS) + Repurposed Structures;
- **Overworld:** Terralith + Tectonic;
- **Nether:** Incendium;
- **End:** Nullscape;
- **survival/QoL:** Universal Graves, FallingTree;
- **карта/администрирование:** BlueMap, Chunky, spark;
- **оптимизации:** Lithium, FerriteCore, ServerCore, Krypton, Alternate Current;
- **библиотеки:** Fabric API и транзитивные зависимости модов.

MVS добавляет 130+ vanilla-style структур и подземелий. Repurposed Structures расширяет семейства существующих ванильных структур по биомам. Оба работают server-side и заменяют ранее использовавшиеся **Dungeons & Taverns** и **Towns & Towers**.

Dungeons & Taverns намеренно не входит в публичный image из-за ограничений на перераспространение. Towns & Towers также убран из базового дистрибутива, чтобы не навязывать форкам условия CC-BY-NC-SA. Базовая сборка ориентируется на зависимости, которые можно законно перераспространять и форкать на понятных условиях.

Terralith, Incendium и Nullscape распространяются **без изменений** как часть modpack в соответствии с Stardust Labs License; требуемая атрибуция и ссылки находятся в [`THIRD_PARTY.md`](THIRD_PARTY.md). Tectonic распространяется по MIT.

Мир, player data и настройки хранятся отдельно в persistent `/data` и не входят в Docker image.

## Docker images

Релиз публикует:

```text
ghcr.io/mirivlad/mymine:<version>
ghcr.io/mirivlad/mymine-landing:<version>
```

Для production рекомендуется конкретный semver tag, а не `latest`.

## Portainer / Docker Compose

Основной переносимый stack — корневой `compose.yml`. Для Portainer его можно использовать напрямую как Git stack и передать значения через Environment variables.

Минимально значимые переменные:

```dotenv
IMAGE_TAG=0.3.0
AUTH_DOMAIN=auth.mymine.example.org
AUTH_BASE_URL=https://auth.mymine.example.org
VERIFY_MINECRAFT_OWNERSHIP=true
DRASL_REQUIRE_INVITE=false
MC_ADDRESS=mymine.example.org:25565
MC_PORT=25565
MAP_URL=/map/
MAP_PORT=44447
BLUEMAP_ACCEPT_DOWNLOAD=false
BLUEMAP_RENDER_THREADS=1
LANDING_PORT=44445
AUTH_PORT=44446
DATA_DIR=/srv/mymine/data
AUTH_DATA_DIR=/srv/mymine/auth-data
MEMORY=4G
CONTAINER_MEMORY_LIMIT=6g
```

`.env.example` содержит полный список доступных параметров.

`auth-config` и `bluemap-config` — init-контейнеры. Состояние `Exited (0)` после успешной генерации конфигурации является нормальным.

`BLUEMAP_ACCEPT_DOWNLOAD=false` оставлен безопасным default. Включайте `true` только после того, как оператор может принять условия BlueMap/Minecraft для загрузки необходимых клиентских ресурсов. Эти ресурсы не входят в репозиторий и Docker image MyMine.

`deploy/portainer-stack.yml` сохраняется как production-пример исходной установки MyMine и содержит её исторические default paths/domains. Для новой переносимой установки предпочтителен корневой `compose.yml` с собственными Environment variables.

## Nginx

Примеры находятся в `deploy/`:

- `nginx-mymine-http.conf` — bootstrap HTTP для Certbot;
- `nginx-mymine.conf` — HTTPS reverse proxy.

Landing, Drasl и BlueMap в рекомендуемой схеме публикуются только на `127.0.0.1`; наружу их отдаёт nginx. Minecraft TCP/25565 проксировать HTTP nginx не требуется.

## Persistent data

Не удаляйте:

```text
DATA_DIR        -> мир, playerdata, настройки Minecraft
AUTH_DATA_DIR   -> база пользователей Drasl и его конфигурация
```

Обновление image/redeploy не должно удалять существующий мир или зарегистрированных игроков.

## Разработка и CI

Проверка compose:

```bash
docker compose -f compose.yml -f compose.dev.yml config
```

Полный локальный smoke test Minecraft:

```bash
./scripts/smoke-test.sh
```

Сборка лаунчера:

```bash
HMCL_VERSION=3.16.3 \
MYMINE_AUTH_URL=https://auth.example.org/ \
MYMINE_SERVER_NAME=MyMine \
MYMINE_SERVER_ADDRESS=mc.example.org:25565 \
./launcher/build.sh
```

GitHub Actions:

- валидирует compose;
- поднимает pinned Drasl отдельно с `VERIFY_MINECRAFT_OWNERSHIP=true` и `false`;
- собирает Minecraft image и landing image;
- запускает Minecraft smoke test с публичным набором модов;
- собирает MyMine Launcher и прогоняет тесты патча HMCL;
- release workflow по semver tag публикует Docker images и launcher assets.

## Лицензии и сторонние компоненты

Собственный код MyMine — deployment/configuration, landing, scripts и прочие компоненты, созданные в рамках проекта — распространяется под **GNU General Public License v3 only (`GPL-3.0-only`)**. Лицензионное объявление находится в [`LICENSE`](LICENSE).

MyMine Launcher основан на **Hello Minecraft! Launcher (HMCL)** и сохраняет применимые условия **GNU GPLv3** и дополнительные требования upstream; соответствующие модифицированные исходники публикуются вместе с release binaries.

Сторонние серверные компоненты и моды **не перелицензируются** под GPL MyMine и сохраняют собственные лицензии. Список прямых компонентов, лицензий, атрибуций и upstream links: [`THIRD_PARTY.md`](THIRD_PARTY.md).

Minecraft является товарным знаком Mojang/Microsoft. MyMine не является официальным продуктом Mojang или Microsoft и не одобрен ими.

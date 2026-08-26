# MyMine

MyMine — воспроизводимый Docker-стек для собственного Minecraft Java сервера с серверными модами, self-hosted авторизацией и готовым лаунчером для игроков.

Проект собран так, чтобы администратор мог развернуть всё через Portainer, а игроку было достаточно зарегистрироваться, скачать MyMine Launcher и установить обычный Minecraft нужной версии.

## Что входит в стек

- **Minecraft Java 26.2 / Fabric** — игровой сервер.
- **Drasl** — собственный Yggdrasil/authlib-совместимый сервер аккаунтов.
- **MyMine Landing** — лендинг, регистрация, инструкции и раздача лаунчера.
- **BlueMap** — браузерная 3D-карта мира, доступная через `/map/`.
- **MyMine Launcher** — сборка HMCL с преднастроенной авторизацией MyMine и без обязательного Microsoft-аккаунта.
- **GitHub Actions** — CI, сборка лаунчера, публикация Docker images и release assets.

```text
Internet
   |
   +-- 80/443 --> nginx
   |                +-- mymine.example.org ------> landing:80
   |                +-- mymine.example.org/map/ -> BlueMap:8100
   |                +-- auth.mymine.example.org -> drasl:25585
   |
   +-- 25565 -------------------------------> minecraft:25565
                                                    |
                                                    +--> Drasl session API
```

## Клиент игрока

Для текущей сборки игроку нужен **обычный Minecraft Java 26.2**.

**Fabric, Forge, NeoForge и клиентские моды устанавливать не нужно.** Сервер сам работает на Fabric, но текущий набор модов является серверным и допускает подключение vanilla-клиента той же версии Minecraft.

Порядок входа:

1. Зарегистрироваться на Drasl/MyMine.
2. Скачать MyMine Launcher с лендинга.
3. В лаунчере добавить аккаунт **MyMine**.
4. Установить Minecraft Java 26.2 без mod loader.
5. Запустить игру и открыть **«Сетевая игра»** — сервер **MyMine** уже будет добавлен в список автоматически. Адрес `mymine.mirv.top:25565` остаётся для ручного подключения и диагностики.

## MyMine Launcher

Лаунчер собирается из HMCL 3.16.3 во время CI. Наш патч минимален и воспроизводим:

- внешний Yggdrasil URL встраивается на этапе сборки;
- `MyMine` становится основным внешним способом входа;
- Microsoft скрыт из списка добавления аккаунта;
- LittleSkin не добавляется новым профилям и удаляется из старых списков;
- ограничение, требующее Microsoft-аккаунт перед external/offline login, отключено;
- обычный offline-аккаунт HMCL остаётся доступен как локальный режим;
- при первом запуске конкретной установки Minecraft сервер MyMine аккуратно добавляется первым в `servers.dat`;
- существующие серверы игрока сохраняются, одинаковый адрес не дублируется;
- добавление выполняется как одноразовая миграция: если игрок потом удалит MyMine из списка, лаунчер не станет навязывать его снова при каждом запуске.

Имя и адрес встроенного сервера задаются при сборке через `MYMINE_SERVER_NAME` и `MYMINE_SERVER_ADDRESS`.

Сборка выполняется скриптом `launcher/build.sh`. Патч находится в `launcher/patch-hmcl.py`.

Release публикует:

```text
MyMineLauncher-3.16.3.exe
MyMineLauncher-3.16.3.deb
MyMineLauncher-3.16.3.jar
MyMineLauncher-3.16.3.sh
MyMineLauncher-3.16.3-source.tar.gz
SHA256SUMS
```

Модифицированные исходники HMCL публикуются вместе с бинарниками в соответствии с GPLv3.

## Серверные моды

Прямые версии модов закреплены в `modrinth-mods.txt`, а зависимости разрешаются при сборке image.

В текущий набор входят Fabric API, Lithium, FerriteCore, ServerCore, Krypton, Alternate Current, spark, Chunky, BlueMap, Universal Graves, FallingTree, Terralith, Tectonic, Incendium, Nullscape, Dungeons and Taverns, Towns and Towers и их необходимые зависимости (включая Polymer для Universal Graves).

Git/image является источником истины для версий Minecraft, Fabric и модов. Мир и player data хранятся отдельно в persistent `/data`.

## Docker images

Релиз публикует два образа:

```text
ghcr.io/mirivlad/mymine:<version>
ghcr.io/mirivlad/mymine-landing:<version>
```

Для production лучше использовать конкретный semver tag, а не `latest`.

## Portainer

Готовый stack находится в:

```text
deploy/portainer-stack.yml
```

Основные переменные:

```dotenv
IMAGE_TAG=0.3.0
AUTH_DOMAIN=auth.mymine.example.org
AUTH_BASE_URL=https://auth.mymine.example.org
MC_ADDRESS=mymine.example.org:25565
MC_PORT=25565
MAP_URL=/map/
MAP_PORT=44447
BLUEMAP_ACCEPT_DOWNLOAD=false
BLUEMAP_RENDER_THREADS=1
LANDING_PORT=44445
AUTH_PORT=44446
DATA_DIR=/home/user/mymine/data
AUTH_DATA_DIR=/home/user/mymine/auth-data
MEMORY=4G
CONTAINER_MEMORY_LIMIT=6g
```

`AUTH_BASE_URL` используется стеком и release-сборкой лаунчера. Адрес, который лаунчер добавляет в «Сетевую игру», задаётся отдельно через build-time `MYMINE_SERVER_ADDRESS`.

`auth-config` и `bluemap-config` являются init-контейнерами. Состояние `Exited (0)` после генерации конфигурации является нормальным.

BlueMap требует отдельного подтверждения `accept-download`. По умолчанию `BLUEMAP_ACCEPT_DOWNLOAD=false`. Установите `true` только если можете принять условия BlueMap для загрузки клиентских ресурсов Minecraft. Число потоков рендера по умолчанию ограничено одним через `BLUEMAP_RENDER_THREADS=1`.

## Nginx

Примеры находятся в `deploy/`:

- `nginx-mymine-http.conf` — bootstrap HTTP для Certbot;
- `nginx-mymine.conf` — итоговый HTTPS reverse proxy.

Landing, Drasl и BlueMap публикуются Docker'ом только на `127.0.0.1`. В готовом nginx-конфиге карта проксируется как `https://mymine.mirv.top/map/` на локальный порт `44447`; отдельный поддомен и новый внешний порт не нужны. Minecraft TCP 25565 проксировать HTTP nginx не требуется.

## Persistent data

Не удаляйте эти каталоги при обновлении image:

```text
DATA_DIR        -> мир, playerdata, настройки Minecraft
AUTH_DATA_DIR   -> база пользователей Drasl и его конфигурация
```

Обновление `IMAGE_TAG` и redeploy не должно удалять зарегистрированных игроков или существующий мир.

## Разработка и CI

Локальная проверка Docker-части:

```bash
docker compose -f compose.yml -f compose.dev.yml config
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

GitHub Actions проверяет compose, собирает Minecraft image, landing image и MyMine Launcher. В тесты лаунчера входит проверка миграции `servers.dat`: MyMine добавляется первым, не дублируется и не возвращается после осознанного удаления игроком. Release workflow по semver tag публикует Docker images и прикладывает сборки лаунчера к GitHub Release.

## Лицензии

Код и конфигурация MyMine находятся в этом репозитории. MyMine Launcher основан на **Hello Minecraft! Launcher (HMCL)** и распространяется на условиях **GNU GPLv3**; модифицированные исходники публикуются вместе с релизом.

Minecraft является товарным знаком Mojang/Microsoft. MyMine не является официальным продуктом Mojang или Microsoft.

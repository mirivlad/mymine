# MyMine

MyMine — воспроизводимый Docker-стек для собственного Minecraft Java сервера: Fabric-сервер с server-side модами, self-hosted авторизация Drasl, web-регистрация, BlueMap и готовая сборка HMCL для игроков.

Цель проекта — дать администратору цельный серверный комплект, который можно развернуть через Docker Compose / Portainer, а игрокам оставить обычный Minecraft-клиент без ручной установки Fabric и modpack.

## Что входит в стек

- **Minecraft Java 26.3 / Fabric** — игровой сервер;
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

`DRASL_REQUIRE_INVITE=true` — безопасный режим по умолчанию для новой установки. На пустой базе Drasl печатает первоначальную invite-ссылку в лог; по ней оператор регистрирует первый аккаунт. До первого запуска обязательно задайте `DRASL_ADMIN` — имя пользователя, которое должно получить права администратора. Имя администратора намеренно не имеет универсального default, чтобы публичная установка не оставляла гонку за заранее известный аккаунт `admin`.

После создания первого администратора приглашения можно оставить обязательными или явно переключить `DRASL_REQUIRE_INVITE=false`, если нужна открытая регистрация.

Переключение режима регистрации не удаляет уже существующие аккаунты Drasl; оно меняет правила создания/импорта новых профилей.

## Клиент игрока

Для текущей сборки нужен **Minecraft Java 26.3**.

**Клиентские моды необязательны.** Сервер работает на Fabric, но поддерживает обычный Minecraft Java 26.3 без модов. Forge/NeoForge в клиентской сборке MyMine не используются.

Для красивой графики: в MyMine Launcher установите **Minecraft Java 26.3 + Fabric Loader 0.20.1**. При первом запуске этого профиля лаунчер автоматически скачивает через Modrinth (с проверкой SHA-512) Sodium, Iris, ImmediatelyFast, Entity Culling, Mod Menu, Sodium Extra, Reese's Sodium Options и обязательные зависимости. Также он добавляет **Complementary Reimagined, Complementary Unbound, BSL, MakeUp Ultra Fast** в `shaderpacks`, а **Faithful 32x, Classic Faithful 32x, Faithful 64x** в `resourcepacks`.

Шейдеры и текстуры не активируются принудительно: после запуска выберите один набор в настройках графики Minecraft. По умолчанию картинка остаётся обычной — для совместимости со слабыми видеокартами. Подготовленный пакет можно также импортировать в поддерживающий Modrinth-формат лаунчер из файла `MyMine-26.3.mrpack` с лендинга. Для первой загрузки требуется интернет, скачанные ресурсы принадлежат их авторам и не зеркалируются MyMine.

Порядок входа:

1. Зарегистрироваться на Drasl/MyMine в соответствии с выбранной администратором политикой.
2. Скачать MyMine Launcher с лендинга.
3. Добавить аккаунт **MyMine**.
4. Установить Minecraft Java 26.3 без модлоадера, либо профиль Fabric 26.3 для шейдеров.
5. Запустить игру и открыть «Сетевая игра» — адрес MyMine добавляется лаунчером в список один раз.

**Версию Minecraft при установке указывать не нужно.** Достаточно выбрать IMAGE_TAG (0.4.10 или latest): каждая редакция использует собственную встроенную версию Minecraft, а лендинг опрашивает запущенный сервер при сборке. Старый MC_VERSION из Portainer игнорируется. Устаревший автоматически сгенерированный MOTD с номером версии исправляется при старте с использованием версии встроенного сервера.

**Minecraft 26.3 и Drasl 4.0.1:** authlib 10 запрашивает URL проверки игровых сессий через Minecraft Services discovery. minecraft.api.discovery.host настроен автоматически. Образ Drasl закреплён по digest; его обновление выполняет миграцию базы 5→6 с резервной копией. Перед переходом рекомендуется отдельно сохранить AUTH_DATA_DIR и мир (DATA_DIR).

**Живая версия Minecraft на лендинге и в MOTD.** Сервер сам подставляет версию из собранного образа в MOTD (стандартная строка MyMine — Minecraft {version}; для собственного описания можно использовать {version}). Старые описания с 26.2 исправляются автоматически при запуске. На лендинге встроенный фоновый опросчик проверяет Minecraft по внутреннему адресу minecraft:25565 каждые 45 секунд и обновляет server.json. Все шесть шаблонов страницы обновляют версию без её перезагрузки. Пока сервер недоступен, остаётся последняя известная версия или версия сборки. Ссылки на конкретные версии клиентских пакетов при этом не меняются.

Версия лаунчера **не задаётся в Compose/Portainer**: при запуске лендинг сам находит единственный `MyMineLauncher-*.jar` внутри своего образа, извлекает версию для ссылок и убеждается, что файлы EXE/DEB/SH и исходники существуют. Даже старое значение переменной `HMCL_VERSION` игнорируется. Версия `HMCL_VERSION` нужна только **при сборке** форка HMCL, но не при его развёртывании.

## MyMine Launcher

Лаунчер собирается из HMCL 3.16.4 во время CI. Патч воспроизводим и хранится в `launcher/patch-hmcl.py`.

Изменения MyMine:

- внешний Yggdrasil URL встраивается на этапе сборки;
- MyMine становится основным внешним способом входа;
- Microsoft скрыт из списка добавления аккаунта **после того, как отдельная регистрация Drasl уже выполнена**;
- LittleSkin не добавляется новым профилям и удаляется из старых списков;
- ограничение HMCL, требующее Microsoft-аккаунт перед external/offline login, отключено;
- обычный offline-аккаунт HMCL остаётся доступен как локальный режим;
- штатная проверка обновлений HMCL отключена: её подпись не подходит модифицированному лаунчеру, а обновления MyMine распространяются через страницу своего экземпляра и GitHub Releases;
- при первом запуске конкретной установки Minecraft сервер MyMine добавляется первым в `servers.dat`;
- в профиле Fabric 26.3 автоматически устанавливается клиентский пакет оптимизаций и появляются шейдеры/текстурпаки на выбор;
- существующие серверы сохраняются, адрес не дублируется;
- миграция выполняется один раз: если игрок позже удалит MyMine из списка, лаунчер не добавит его снова принудительно.

Имя и адрес экземпляра задаются при сборке базового launcher artifact:

```text
MYMINE_SERVER_NAME
MYMINE_SERVER_ADDRESS
MYMINE_AUTH_URL
```

При этом Docker image лендинга **не раздаёт эти базовые значения вслепую**. При старте конкретной установки он берёт её `AUTH_BASE_URL`, `MC_ADDRESS` и `SERVER_NAME`, внедряет их в ресурс `mymine-instance.properties` внутри `.exe`, `.jar`, `.sh` и `.deb`, а затем пересчитывает `SHA256SUMS`. Поэтому launcher, скачанный с конкретного MyMine landing, подключается к auth и Minecraft именно этой установки. Для этого форку не нужен собственный Java toolchain или отдельная сборка HMCL.

GitHub Release assets используют значения текущего репозитория (для официального MyMine — `auth.mymine.mirv.top` и `mymine.mirv.top:25565`). Форк при желании может задать repository variables `MYMINE_AUTH_URL`, `MYMINE_SERVER_NAME`, `MYMINE_SERVER_ADDRESS` и получить свои значения также в GitHub Release assets.

Release публикует:

```text
MyMineLauncher-3.16.4.exe
MyMineLauncher-3.16.4.deb
MyMineLauncher-3.16.4.jar
MyMineLauncher-3.16.4.sh
MyMineLauncher-3.16.4-source.tar.gz
MyMine-26.3.mrpack
SHA256SUMS
```

Модифицированное дерево исходников HMCL публикуется вместе с бинарниками в соответствии с GPLv3.

Debian artifact устанавливается как пакет `mymine-launcher`, создаёт `/usr/bin/mymine-launcher` и desktop entry **MyMine Launcher**. Пакет объявляет замену старого upstream-named пакета `hmcl`, использовавшегося в MyMine до полного Debian-ребрендинга; wrapper сохраняет доступ к его существующему пользовательскому каталогу настроек при обновлении.

## Обновление сервера с Minecraft 26.2 на 26.3

**Перед обновлением создайте полную резервную копию `DATA_DIR` и `AUTH_DATA_DIR`, когда Minecraft выключен.** Minecraft может обновить структуру мира при первом запуске, и обратный запуск старой версии не поддерживается. Особое внимание: Incendium 5.5.4 для 26.3 у автора помечен как **alpha**; перед применением обновления проверьте запуск на копии сохранённого мира. В MyMine используются Fabric JAR-варианты Terralith, Nullscape и Incendium, не их datapack ZIP.

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
### Переключение Classic / Engineering одной переменной

Начиная с **MyMine 0.4.11**, один Portainer-стек поддерживает две редакции:

| MYMINE_EDITION | Minecraft / загрузчик | Модификации | Сохранение |
| --- | --- | --- | --- |
| classic (по умолчанию) | 26.3, Fabric | нынешний игровой мир и серверные моды | data (старый мир, через ссылку data-classic) |
| engineering | 1.21.1, NeoForge | Create Aeronautics, Create, Sable, MineColonies | data-engineering (отдельный мир) |

В Portainer достаточно изменить **MYMINE_EDITION=classic** на **MYMINE_EDITION=engineering** и нажать Update Stack с обновлением образов. Не нужно устанавливать MC_VERSION, VERSION, TYPE или редактировать список модов; Compose выбирает образ ghcr.io/mirivlad/mymine:classic-<тег> либо engineering-<тег>. Тег latest имеет две независимые редакции: classic-latest и engineering-latest. Существующий ghcr.io/mirivlad/mymine:latest остаётся Classic для обратной совместимости.

При первом обновлении init-контейнер world-config создаёт только символьную ссылку data-classic → data и отдельный каталог data-engineering. Старый мир не переносится и не копируется. Каждый серверный контейнер получает **только один каталог сохранений**. При возврате в Classic старый мир доступен без изменений. Переключение перезапускает Minecraft: уведомите игроков и сделайте резервную копию.

Для переносимого стека MYMINE_WORLDS_ROOT должен быть родительским каталогом DATA_DIR; например MYMINE_WORLDS_ROOT=/srv/mymine, DATA_DIR=/srv/mymine/data. Несовпадение блокирует запуск, а не создаёт случайный пустой мир. На tomas используются прежние пути /home/mirivlad/mymine и /home/mirivlad/mymine/data.

**Клиент:** лендинг автоматически выбирает редакцию. Для Engineering он показывает отдельную страницу и отдаёт MyMine Launcher (Windows EXE, Linux DEB, Java JAR). В лаунчере встроен проверенный профиль Modrinth: при первом запуске Engineering штатный установщик HMCL загружает Minecraft 1.21.1, NeoForge 21.1.265 и нужные моды без затрагивания старых профилей. Профиль MRPACK также доступен отдельным файлом для других лаунчеров. Потребуется Java 21 для игры и интернет для первоначального скачивания; чужие JAR не включены в архив лаунчера.

**Память:** на tomas менее 8 ГиБ ОЗУ, поэтому переключение в одном стеке безопаснее параллельного запуска двух тяжёлых Minecraft. Для Engineering остаётся лимит JVM 4 ГиБ по умолчанию.

**Проверки:** CI подтверждает, что NeoForge 1.21.1 успешно запускается с Create Aeronautics и MineColonies. Вход реального клиента через Drasl и взаимодействие техники с жителями требуют отдельной игровой проверки.


Основной переносимый stack — корневой `compose.yml`. Для Portainer его можно использовать напрямую как Git stack и передать значения через Environment variables.

Минимально значимые переменные:

```dotenv
IMAGE_TAG=0.4.11
MYMINE_EDITION=classic
MYMINE_WORLDS_ROOT=/srv/mymine
AUTH_DOMAIN=auth.mymine.example.org
AUTH_BASE_URL=https://auth.mymine.example.org
DRASL_ADMIN=mymine-admin
VERIFY_MINECRAFT_OWNERSHIP=true
DRASL_REQUIRE_INVITE=true
MC_ADDRESS=mymine.example.org:25565
SERVER_NAME=MyMine
LANDING_TEMPLATE=adventure
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

### Шаблоны лендинга

Внешний вид landing выбирается без пересборки image:

```dotenv
LANDING_TEMPLATE=adventure
```

Доступны шесть вариантов:

- `showcase` — кинематографичный шаблон-витрина с крупным hero и тремя фотосекциями; поддерживает установочные изображения через переменные;
- `adventure` — иллюстрированный атмосферный вариант с крупным hero-изображением; используется по умолчанию;
- `atlas` — светлый картографический вариант с BlueMap в центре композиции;
- `modern` — чистый тёмный продуктовый дизайн без внешних иллюстраций;
- `terminal` — консольный/техно-вариант;
- `classic` — прежний лендинг для обратной совместимости.

Иллюстрации в `adventure` и `atlas` входят в image локально, без внешних CDN. `showcase` по умолчанию использует те же встроенные изображения, но его четыре кадра можно подменить изображениями конкретного сервера без пересборки image. Используются только материалы с CC0; происхождение и преобразования перечислены в `landing/assets/ATTRIBUTION.txt` и доступны на работающем лендинге по `/assets/ATTRIBUTION.txt`.

После изменения переменной достаточно redeploy/recreate контейнера `landing`. Мир Minecraft, Drasl и launcher artifacts при переключении шаблона не меняются. Неизвестное имя шаблона считается ошибкой конфигурации, и контейнер завершится с подсказкой допустимых значений.

Для собственных кадров `showcase` положите изображения в `LANDING_ASSETS_DIR` и укажите URL внутри `/custom`:

```dotenv
LANDING_TEMPLATE=showcase
LANDING_ASSETS_DIR=/srv/mymine/landing-assets
LANDING_HERO_IMAGE=/custom/hero.webp
LANDING_GALLERY_IMAGE_1=/custom/night.webp
LANDING_GALLERY_IMAGE_2=/custom/river.webp
LANDING_GALLERY_IMAGE_3=/custom/rainbow.webp
```

Если выбранный шаблон уже присутствует в текущем landing image, после изменения переменных достаточно recreate/redeploy. Если шаблон появился в более новой версии MyMine, сначала обновите `IMAGE_TAG`/landing image и выполните pull, затем redeploy. При использовании `latest` также нужен pull, иначе Docker может оставить уже загруженный локальный image.

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
HMCL_VERSION=3.16.4 \
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


## MyMine Engineering (experimental)

Optional, separate NeoForge 1.21.1 world with Create Aeronautics, MineColonies and Create,
without changing the existing Minecraft 26.3 world. The official client
profile is a small [MyMine Engineering .mrpack](engineering/releases/MyMine-Engineering-0.1.0.mrpack)
that references original upstream files, with pinned cryptographic checksums.
See [Engineering setup and memory safeguards](engineering/README.md) for details.
Never run both heavyweight servers on low-memory hosts (tomas has ~8 GiB RAM).
The engineering world is not started or exposed automatically.

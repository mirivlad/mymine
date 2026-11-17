# MyMine Engineering

Experimental, optional Minecraft **1.21.1 / NeoForge 21.1.265 / Java 21** world with **Create Aeronautics + MineColonies**. The original Fabric 26.3 world remains intact. No downgrade or migration of world data is attempted.

## Mod set

| Mod | Version |
| --- | --- |
| Create | 6.0.10 (includes Flywheel 1.0.6, Ponder 1.0.82 and Registrate as nested JARs) |
| Sable | 2.0.6 |
| Create Aeronautics | 1.3.2 |
| MineColonies | 1.1.1403 |
| Structurize | 1.0.839 |
| BlockUI | 1.0.212 |
| Domum Ornamentum | 1.0.237 |
| MultiPiston | 1.2.58 |
| FerriteCore | 7.0.3 |
| FallingTree (server) | 1.21.1.11 |
| Time Control (server + client) | 1.6.0 |
| Xaero's Minimap (client) | 26.6.0 |
| Xaero's World Map (client) | 1.47.0 |

Each JAR is pinned to an **official CurseForge file ID**, downloaded from CurseForge's own CDN and checked for ZIP integrity. No third-party mod binaries are included in the public repository. The generator records SHA-1/SHA-256/SHA-512 hashes for subsequent verification. Do not mix these NeoForge jars with the existing Fabric instance.

## Prepare the server and client pack

From the repository root:

    python3 engineering/build_pack.py

This populates the ignored engineering/mods/ folder, writes engineering/mods.lock.json, and creates an installable engineering/dist/MyMine-Engineering-0.2.0.mrpack. The .mrpack includes only URLs and checksums (not third-party JARs). On later runs:

    python3 engineering/build_pack.py --verify

For the client, import the .mrpack into **MyMine Launcher / HMCL**, Prism or another compatible launcher to make a separate NeoForge **1.21.1** installation, with Java **21**. Use a separate game directory. The launcher includes 12 client JARs; the server has 11. FallingTree is server-only, Xaero maps client-only. Allocate 5–6 GiB RAM on a client PC if available. In HMCL add a MyMine Drasl account and select the new profile.

## Готовое переключение в Portainer (рекомендуется)

Начиная с MyMine v0.4.11 Engineering входит в официальный стек Portainer. Чтобы переключить мир, установите MYMINE_EDITION=engineering и выполните Update Stack с обновлением образов. Ручная установка NeoForge и серверных JAR больше не нужна.

Лендинг автоматически переключается на страницу Engineering 1.21.1, лаунчер содержит установочный профиль, а мир хранится в отдельном каталоге data-engineering. Для возврата поставьте MYMINE_EDITION=classic.

Следующая инструкция описывает отдельный экспериментальный Compose для разработчиков; обычным администраторам Portainer он больше не нужен.

## Safe trial on tomas

The test world lives only in engineering/data/ (ignored by Git). The optional compose now pulls the curated Engineering image with server-only JAR selection; it does not mount client map mods into a dedicated server. It connects to the existing mymine_default Docker network so the existing **Drasl** service can authenticate players. It does not change the existing Minecraft server, Drasl database or public landing, and the test port binds to **127.0.0.1:25566** by default — not exposed on the public Internet.

**Critical memory limitation:** tomas has ~7.7 GiB total RAM and the current server already uses ~3 GiB. The start script blocks accidentally running both heavyweight worlds simultaneously. After confirming no players are online, stop only the current Minecraft container (its volume is preserved; leave Drasl and landing running):

    docker stop mymine
    ./engineering/start.sh
    docker logs -f mymine-engineering

The engineering JVM defaults to 4 GiB, with a 5 GiB container memory limit. Server-required mod JARs are baked into the image and synchronized into the independent /data/mods directory by the itzg entrypoint. To stop the experimental server:

    docker compose -p mymine-engineering -f engineering/compose.yml down

To return to the current MyMine world:

    docker start mymine

Check the server logs and client compatibility before opening any public game port. The old world cannot be safely loaded into Minecraft 1.21.1. Do not change the original Portainer stack's Minecraft version or mount its data directory for Engineering.

## Controlled world pre-generation (0.4.13)

Chunky 1.4.23 is installed server-side only; players retain their Engineering 0.2.0 client pack. On a quiet server, back up the world, then send commands from the Docker host:

    docker exec mymine rcon-cli chunky world minecraft:overworld
    docker exec mymine rcon-cli chunky shape circle
    docker exec mymine rcon-cli chunky spawn
    docker exec mymine rcon-cli chunky radius 512
    docker exec mymine rcon-cli chunky start

Observe using chunky progress; stop with chunky pause (resumable). Never issue chunky trim, which deletes world chunks. RCON is enabled with a generated password within the container only and is not published on any host port.

## Gameplay improvements in 0.4.12

- FallingTree: chop one natural tree log with an axe to fell the whole tree. The mod runs on the server; clients need no installation. Sneaking suppresses tree-felling by default.
- Maps: Xaero's Minimap (settings: Y, waypoints: B) + Xaero's World Map (M) install with the new HMCL profile MyMine Engineering 0.2.0. Maps are client-only and retain explored terrain locally.
- Day and night: Time Control 1.6.0 makes each in-game daytime last 20 minutes and night 10 minutes. The game tick rate stays at normal speed; farms and colonies are not accelerated. Portainer environment MYMINE_DAY_MINUTES=20 and MYMINE_NIGHT_MINUTES=10 controls the ratio. Values are applied at server start.
- UDP: Minecraft TCP and Sable UDP both publish the same game port, normally 25565, through Docker. Ensure both protocols are allowed by the host firewall and router.
- Upgrade: Download the updated MyMine launcher from Engineering landing. Its versioned profile is new and does not replace the old 0.1.0 instance. Existing players need to select the new 0.2.0 profile.

## Important limitations

- Create Aeronautics requires both **Create and Sable** on NeoForge 1.21.1. MineColonies requires **Structurize, BlockUI, Domum Ornamentum, MultiPiston**.
- Authors report graphical incompatibilities between Aeronautics and **Iris Shaders**. Test without shaders.
- Two mods coexisting does not mean MineColonies NPCs can pilot flying vehicles or handle Create logistics automatically. Those integrations would require gameplay tests, and possibly extra mods or custom code.
- A real HMCL/Drasl multiplayer login has now been confirmed on tomas (2026-11-17).

Official sources: https://www.curseforge.com/minecraft/mc-mods/create-aeronautics , https://www.curseforge.com/minecraft/mc-mods/minecolonies , https://www.curseforge.com/minecraft/mc-mods/create , https://www.curseforge.com/minecraft/mc-mods/sable .

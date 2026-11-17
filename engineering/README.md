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

Each JAR is pinned to an **official CurseForge file ID**, downloaded from CurseForge's own CDN and checked for ZIP integrity. No third-party mod binaries are included in the public repository. The generator records SHA-1/SHA-256/SHA-512 hashes for subsequent verification. Do not mix these NeoForge jars with the existing Fabric instance.

## Prepare the server and client pack

From the repository root:

    python3 engineering/build_pack.py

This populates the ignored engineering/mods/ folder, writes engineering/mods.lock.json, and creates an installable engineering/dist/MyMine-Engineering-0.1.0.mrpack. The .mrpack includes only URLs and checksums (not third-party JARs). On later runs:

    python3 engineering/build_pack.py --verify

For the client, import the .mrpack into **MyMine Launcher / HMCL**, Prism or another compatible launcher to make a separate NeoForge **1.21.1** installation, with Java **21**. Use a separate game directory. All nine mods must match the server. Allocate 5–6 GiB RAM on a client PC if available. In HMCL add a MyMine Drasl account and select the new profile.

## Готовое переключение в Portainer (рекомендуется)

Начиная с MyMine v0.4.11 Engineering входит в официальный стек Portainer. Чтобы переключить мир, установите MYMINE_EDITION=engineering и выполните Update Stack с обновлением образов. Ручная установка NeoForge и серверных JAR больше не нужна.

Лендинг автоматически переключается на страницу Engineering 1.21.1, лаунчер содержит установочный профиль, а мир хранится в отдельном каталоге data-engineering. Для возврата поставьте MYMINE_EDITION=classic.

Следующая инструкция описывает отдельный экспериментальный Compose для разработчиков; обычным администраторам Portainer он больше не нужен.

## Safe trial on tomas

The test world lives only in engineering/data/ (ignored by Git). It connects to the existing mymine_default Docker network so the existing **Drasl** service can authenticate players. It does not change the existing Minecraft server, Drasl database or public landing, and the test port binds to **127.0.0.1:25566** by default — not exposed on the public Internet.

**Critical memory limitation:** tomas has ~7.7 GiB total RAM and the current server already uses ~3 GiB. The start script blocks accidentally running both heavyweight worlds simultaneously. After confirming no players are online, stop only the current Minecraft container (its volume is preserved; leave Drasl and landing running):

    docker stop mymine
    ./engineering/start.sh
    docker logs -f mymine-engineering

The engineering JVM defaults to 4 GiB, with a 5 GiB container memory limit. Mod JARs are mounted read-only at /mods and synchronized into the independent /data/mods directory by the itzg entrypoint; the server never writes to the verified upstream mod cache. To stop the experimental server:

    docker compose -p mymine-engineering -f engineering/compose.yml down

To return to the current MyMine world:

    docker start mymine

Check the server logs and client compatibility before opening any public game port. The old world cannot be safely loaded into Minecraft 1.21.1. Do not change the original Portainer stack's Minecraft version or mount its data directory for Engineering.

## Important limitations

- Create Aeronautics requires both **Create and Sable** on NeoForge 1.21.1. MineColonies requires **Structurize, BlockUI, Domum Ornamentum, MultiPiston**.
- Authors report graphical incompatibilities between Aeronautics and **Iris Shaders**. Test without shaders.
- Two mods coexisting does not mean MineColonies NPCs can pilot flying vehicles or handle Create logistics automatically. Those integrations would require gameplay tests, and possibly extra mods or custom code.
- Drasl compatibility with a real client under NeoForge 1.21.1 has not yet been proven on this new world; a full client-to-server login test is mandatory before public launch.

Official sources: https://www.curseforge.com/minecraft/mc-mods/create-aeronautics , https://www.curseforge.com/minecraft/mc-mods/minecolonies , https://www.curseforge.com/minecraft/mc-mods/create , https://www.curseforge.com/minecraft/mc-mods/sable .

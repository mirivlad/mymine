# Third-party components

MyMine's own deployment/configuration, landing and supporting code is licensed under **GNU GPL v3 only (`GPL-3.0-only`)**. Every third-party component keeps its upstream copyright and license; inclusion here does **not** relicense third-party code or assets under MyMine's GPL license.

The Minecraft server image is built reproducibly from the exact direct Modrinth version IDs in `modrinth-mods.txt`. Required transitive dependencies are resolved by `mc-image-helper`; those dependencies retain their own upstream licenses and notices.

## Server image and infrastructure

| Component | Role | Upstream license | Upstream |
|---|---|---|---|
| itzg/docker-minecraft-server | Base Minecraft server image/tooling | Apache-2.0 | https://github.com/itzg/docker-minecraft-server |
| Fabric Loader | Mod loader | Apache-2.0 | https://github.com/FabricMC/fabric-loader |
| Fabric API | Fabric APIs | Apache-2.0 | https://modrinth.com/mod/fabric-api |
| Drasl | Self-hosted Yggdrasil/auth server | GPL-3.0 | https://github.com/unmojang/drasl |
| nginx | Landing/reverse-proxy base software | BSD-2-Clause | https://nginx.org/ |

Minecraft server software, assets and trademarks remain subject to Mojang/Microsoft terms. Setting `EULA=TRUE` in the container means the server operator accepts the Minecraft EULA; MyMine does not redistribute the proprietary Minecraft client.

## Direct Minecraft mods

The following are direct entries in `modrinth-mods.txt`. They are downloaded unmodified.

| Component | Purpose | License | Upstream |
|---|---|---|---|
| Fabric API | Fabric APIs | Apache-2.0 | https://modrinth.com/mod/fabric-api |
| Lithium | Server/game-logic optimization | LGPL-3.0-only | https://modrinth.com/mod/lithium |
| FerriteCore | Memory optimization | MIT | https://modrinth.com/mod/ferrite-core |
| ServerCore | Server optimization | MIT | https://modrinth.com/mod/servercore |
| Krypton | Networking optimization | LGPL-3.0 | https://github.com/astei/krypton |
| Alternate Current | Redstone optimization | MIT | https://modrinth.com/mod/alternate-current |
| spark | Profiler | GPL-3.0-only | https://modrinth.com/mod/spark |
| Chunky | Chunk pre-generation | GPL-3.0-only | https://modrinth.com/plugin/chunky |
| BlueMap | Browser 3D map | MIT | https://modrinth.com/plugin/bluemap |
| Universal Graves | Graves / inventory recovery | LGPL-3.0-only | https://modrinth.com/mod/universal-graves |
| FallingTree | Server-side tree cutting | LGPL-3.0-only | https://modrinth.com/mod/fallingtree |
| Tectonic | Terrain shaping | MIT | https://modrinth.com/datapack/tectonic |
| Moog's Voyager Structures (MVS) | 130+ vanilla-style structures/dungeons | MIT | https://modrinth.com/mod/moogs-voyager-structures |
| Repurposed Structures (Fabric) | Vanilla structure variants | LGPL-3.0-only | https://modrinth.com/mod/repurposed-structures-fabric |
| Terralith | Overworld world generation | Stardust Labs License | https://modrinth.com/datapack/terralith |
| Incendium Legacy | Nether world generation/adventure | Stardust Labs License | https://modrinth.com/datapack/incendium |
| Nullscape | End world generation | Stardust Labs License | https://modrinth.com/datapack/nullscape |

### Stardust Labs attribution

MyMine distributes **Terralith, Incendium and Nullscape unmodified as part of the server modpack**.

Credit: **Stardust Labs**

- Terralith: https://modrinth.com/datapack/terralith
- Incendium: https://modrinth.com/datapack/incendium
- Nullscape: https://modrinth.com/datapack/nullscape
- Stardust Labs: https://www.stardustlabs.net/
- License reference: https://github.com/Stardust-Labs-MC/Terralith/blob/1.20/license.txt

The Stardust Labs License permits unmodified Stardust Labs mods/datapacks in a publicly distributed modpack when credit and a link to the relevant project are provided. It does **not** permit standalone redistribution or public redistribution of modified copies without the permissions described by that license. Fork maintainers must preserve this attribution and must re-check the current upstream license before changing how these files are packaged.

### GPL components

`spark`, `Chunky` and Drasl are GPL-licensed software. MyMine does not modify their source code, but a distributor of binary/container artifacts still needs to satisfy the applicable GPL source/notice requirements for the exact versions it conveys. Fork/release maintainers should therefore preserve upstream license notices and ensure corresponding source remains available for the versions shipped by their release.

The custom MyMine Launcher is a separate GPL-derived work and is handled below.

## MyMine Launcher / HMCL

MyMine Launcher is based on **Hello Minecraft! Launcher (HMCL)**:

- upstream: https://github.com/HMCL-dev/HMCL
- upstream license: GNU GPLv3 plus HMCL's additional distribution requirements
- pinned upstream version: see `HMCL_VERSION` in the build/release workflow
- MyMine patch: `launcher/patch-hmcl.py`

Each MyMine release publishes a source archive generated from the **fully patched HMCL source tree** together with the launcher binaries and `SHA256SUMS`.

## Explicitly excluded from the public base distribution

### Dungeons & Taverns

Dungeons & Taverns was previously part of the private/original MyMine mod list. It is **not** included in the public base image because its redistribution terms require permission from the author. An individual permission granted to one MyMine distributor would not automatically grant downstream forks their own redistribution rights unless that permission explicitly did so.

### Towns & Towers

Towns & Towers was also removed from the base distribution. Its CC-BY-NC-SA-4.0 terms do permit redistribution subject to attribution, non-commercial and share-alike conditions, but MyMine intentionally avoids imposing those additional downstream restrictions on the default forkable server bundle.

MVS (MIT) and Repurposed Structures (LGPL-3.0-only) replace the structure-expansion role of these two projects.

## BlueMap resource download

BlueMap may need to download Minecraft client resources to render maps. MyMine defaults to:

```dotenv
BLUEMAP_ACCEPT_DOWNLOAD=false
```

Those proprietary resources are **not** committed to this repository and are **not** baked into MyMine images. The server operator must explicitly opt in after reviewing the applicable upstream/Minecraft terms.

## Updating this file

When changing `modrinth-mods.txt`, a release maintainer should check at least:

1. that redistribution as part of a public server/modpack is permitted;
2. whether attribution, source-code availability, non-commercial, share-alike or other downstream conditions apply;
3. whether the selected version is server-side / vanilla-client compatible;
4. whether required dependencies introduce additional redistribution conditions;
5. that any required notices remain available in the distributed artifact.

This document is an engineering inventory, not legal advice. Upstream license texts are authoritative.

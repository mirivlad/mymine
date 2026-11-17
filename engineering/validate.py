#!/usr/bin/env python3
"""Offline validation of the Engineering lockfile and published .mrpack."""
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parent
sources = json.loads((ROOT / "mods.sources.json").read_text())
lock = json.loads((ROOT / "mods.lock.json").read_text())
assert len(sources["mods"]) == len(lock["mods"]) == 14
assert sources["pack"] == lock["pack"]
assert lock["pack"]["minecraft"] == "1.21.1"
assert lock["pack"]["neoforge"].startswith("21.1.")
assert {m["name"] for m in sources["mods"]} == {m["name"] for m in lock["mods"]}
assert len({m["filename"] for m in lock["mods"]}) == 14

pack = ROOT / "releases" / "MyMine-Engineering-0.2.0.mrpack"
assert zipfile.is_zipfile(pack), "Missing published .mrpack"
with zipfile.ZipFile(pack) as archive:
    idx = json.loads(archive.read("modrinth.index.json"))
    assert idx["formatVersion"] == 1 and idx["game"] == "minecraft"
    assert idx["dependencies"] == {"minecraft": "1.21.1", "neoforge": "21.1.265"}
    assert len(idx["files"]) == 12
    files = {m["path"].removeprefix("mods/"): m for m in idx["files"]}
    assert sum(m.get("side","both") != "client" for m in lock["mods"]) == 12
    assert sum(m.get("side","both") != "server" for m in lock["mods"]) == 12
    assert lock["pack"]["version"] == "0.2.0"
    chunky = next(m for m in lock["mods"] if m["name"] == "Chunky")
    assert chunky["side"] == "server" and chunky["source"] == "modrinth"
    assert chunky["filename"] == "Chunky-NeoForge-1.4.23.jar"
    assert chunky["url"] == "https://cdn.modrinth.com/data/fALzjamp/versions/LuFhm4eU/Chunky-NeoForge-1.4.23.jar"
    assert chunky["hashes"]["sha512"] == "2db769dd723f243a21e1881e7c9f825e9c193da6f2bed454b70cb6fa9e51c57f63fdcf017c0657bbd26f7bba30815413e27c74d3c7be0783390a96ee9baa4bf7"
    for item in lock["mods"]:
        if item.get("side","both") == "server":
            assert item["filename"] not in files
            continue
        f = files[item["filename"]]
        assert len(f["downloads"]) == 1 and f["downloads"][0] == item["url"]
        assert urlsplit(item["url"]).hostname == "mediafilez.forgecdn.net"
        assert f["hashes"]["sha512"] == item["hashes"]["sha512"]
        assert f["hashes"]["sha1"] == item["hashes"]["sha1"]
        assert f["fileSize"] == item["fileSize"]
        assert all(re.fullmatch("[0-9a-f]{128}", m["hashes"]["sha512"]) for m in [item])
        assert f["env"] == {"client": "required", "server": "unsupported" if item.get("side","both")=="client" else "required"}
    assert "Chunky-NeoForge-1.4.23.jar" not in files
    assert "FallingTree-1.21.1-1.21.1.11.jar" not in files
    assert "overrides/README-MyMine-Engineering.txt" in archive.namelist()
print("Engineering: 14 pinned mods (12 server / 12 client), checksums and sides verified")

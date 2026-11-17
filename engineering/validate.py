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
assert len(sources["mods"]) == len(lock["mods"]) == 9
assert sources["pack"] == lock["pack"]
assert lock["pack"]["minecraft"] == "1.21.1"
assert lock["pack"]["neoforge"].startswith("21.1.")
assert {m["name"] for m in sources["mods"]} == {m["name"] for m in lock["mods"]}
assert len({m["filename"] for m in lock["mods"]}) == 9

pack = ROOT / "releases" / "MyMine-Engineering-0.1.0.mrpack"
assert zipfile.is_zipfile(pack), "Missing published .mrpack"
with zipfile.ZipFile(pack) as archive:
    idx = json.loads(archive.read("modrinth.index.json"))
    assert idx["formatVersion"] == 1 and idx["game"] == "minecraft"
    assert idx["dependencies"] == {"minecraft": "1.21.1", "neoforge": "21.1.265"}
    assert len(idx["files"]) == 9
    files = {m["path"].removeprefix("mods/"): m for m in idx["files"]}
    for item in lock["mods"]:
        f = files[item["filename"]]
        assert len(f["downloads"]) == 1 and f["downloads"][0] == item["url"]
        assert urlsplit(item["url"]).hostname == "mediafilez.forgecdn.net"
        assert f["hashes"]["sha512"] == item["hashes"]["sha512"]
        assert f["hashes"]["sha1"] == item["hashes"]["sha1"]
        assert f["fileSize"] == item["fileSize"]
        assert all(re.fullmatch("[0-9a-f]{128}", m["hashes"]["sha512"]) for m in [item])
        assert f["env"] == {"client": "required", "server": "required"}
    assert "overrides/README-MyMine-Engineering.txt" in archive.namelist()
print("Engineering: pinned nine mods, checksums, client pack and versions verified")

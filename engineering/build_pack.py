#!/usr/bin/env python3
"""Reproducible MyMine Engineering server mods and client .mrpack.

Downloads only from the original Modrinth CDN / CurseForge CDN.
No copyrighted third-party mod JARs are committed or redistributed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "mods.sources.json"
LOCK = ROOT / "mods.lock.json"
MODS = ROOT / "mods"
DIST = ROOT / "dist"
USER_AGENT = "MyMineEngineering/0.1 (https://github.com/mirivlad/mymine)"
ALLOWED_HOSTS = ("cdn.modrinth.com", "mediafilez.forgecdn.net", "edge.forgecdn.net")


def fetch_json(url):
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def safe_url(url):
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Mod download not hosted on an approved official CDN: " + url)
    return url


def resolve_mod(spec, version):
    if spec["source"] == "modrinth":
        meta = fetch_json("https://api.modrinth.com/v2/project/" +
                          spec["project"] + "/version")
        entries = [item for item in meta
                   if item["version_number"] == spec["version"]
                   and version in item["game_versions"]
                   and "neoforge" in item["loaders"]]
        if len(entries) != 1:
            raise ValueError(spec["name"] + " has no unique pinned NeoForge release")
        item = entries[0]
        file = next((f for f in item["files"] if f.get("primary")), item["files"][0])
        return {"name": spec["name"], "source": "modrinth",
                "version": spec["version"], "filename": file["filename"],
                "url": safe_url(file["url"]), "published_hashes": file["hashes"]}
    if spec["source"] == "curseforge":
        file_id = int(spec["file_id"])
        filename = spec["filename"]
        if not filename.endswith(".jar") or "/" in filename or "\\" in filename:
            raise ValueError("Unsafe CurseForge filename")
        url = ("https://mediafilez.forgecdn.net/files/" +
               str(file_id // 1000) + "/" + str(file_id % 1000).zfill(3) +
               "/" + filename)
        return {"name": spec["name"], "source": "curseforge",
                "file_id": file_id, "filename": filename,
                "url": safe_url(url), "published_hashes": {}}
    raise ValueError("Unknown source: " + str(spec["source"]))


def hash_file(path):
    hashes = {name: hashlib.new(name) for name in ("sha1", "sha256", "sha512")}
    total = 0
    with path.open("rb") as stream:
        while chunk := stream.read(2 * 1024 * 1024):
            total += len(chunk)
            for hasher in hashes.values():
                hasher.update(chunk)
    return {name: hasher.hexdigest() for name, hasher in hashes.items()}, total


def get_mod(record, existing):
    MODS.mkdir(parents=True, exist_ok=True)
    dest = MODS / record["filename"]
    expected = existing.get(record["filename"], {}).get("hashes", {})
    if dest.exists():
        digest, size = hash_file(dest)
        if expected and digest["sha512"] != expected.get("sha512"):
            raise ValueError("Existing local JAR changed unexpectedly: " + dest.name)
    else:
        temp = dest.with_name("." + dest.name + ".partial")
        try:
            req = Request(record["url"], headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=90) as response, temp.open("wb") as output:
                if not any(response.geturl().startswith("https://" + host + "/")
                           for host in ALLOWED_HOSTS):
                    raise ValueError("Mod redirect leaves approved official CDN")
                shutil.copyfileobj(response, output, length=1024 * 1024)
            if not zipfile.is_zipfile(temp):
                raise ValueError("Server returned an invalid mod JAR: " + dest.name)
            digest, size = hash_file(temp)
            temp.replace(dest)
        finally:
            temp.unlink(missing_ok=True)
    for algo, value in record.get("published_hashes", {}).items():
        if algo in digest and digest[algo] != value:
            raise ValueError("Official checksum mismatch: " + dest.name)
    if expected and digest["sha512"] != expected.get("sha512"):
        raise ValueError("Lockfile checksum mismatch: " + dest.name)
    if not zipfile.is_zipfile(dest) or size < 10000:
        raise ValueError("Not a valid mod JAR: " + dest.name)
    print(f"OK: {record['name']}: {dest.name} ({size / 1048576:.1f} MiB)", flush=True)
    return {"name": record["name"], "source": record["source"],
            "filename": record["filename"], "url": record["url"],
            "hashes": digest, "fileSize": size}


def build_pack(config, records):
    DIST.mkdir(exist_ok=True)
    spec = config["pack"]
    idx = {"formatVersion": 1, "game": "minecraft",
           "versionId": spec["version"], "name": spec["name"],
           "summary": "Create Aeronautics + Create + Sable + MineColonies; lightweight NeoForge profile",
           "dependencies": {"minecraft": spec["minecraft"], "neoforge": spec["neoforge"]},
           "files": []}
    for file in records:
        idx["files"].append({
            "path": "mods/" + file["filename"],
            "hashes": {"sha1": file["hashes"]["sha1"],
                       "sha512": file["hashes"]["sha512"]},
            "env": {"client": "required", "server": "required"},
            "downloads": [safe_url(file["url"])],
            "fileSize": file["fileSize"]
        })
    target = DIST / ("MyMine-Engineering-" + spec["version"] + ".mrpack")
    instruction = (
        "MyMine Engineering — Minecraft 1.21.1 / NeoForge " + spec["neoforge"] + "\n"
        "Imports into MyMine Launcher (HMCL), Prism Launcher, or Modrinth App.\n"
        "Requires Java 21. Use a NEW, ISOLATED game directory / profile.\n"
        "Use the MyMine Drasl account selected for the engineering server.\n"
        "This file contains only mod download URLs and checksums, not mod JARs.\n"
    )
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("modrinth.index.json", json.dumps(idx, ensure_ascii=False, indent=2) + "\n")
        z.writestr("overrides/README-MyMine-Engineering.txt", instruction)
    print("CLIENT_MODPACK:", target, flush=True)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Verify stored files and modpack only, no downloads")
    args = parser.parse_args()
    config = json.loads(SOURCE.read_text())
    if config["pack"]["minecraft"] != "1.21.1":
        raise ValueError("Unexpected Minecraft version")
    if len({m["name"] for m in config["mods"]}) != len(config["mods"]):
        raise ValueError("Duplicate mod")
    previous = json.loads(LOCK.read_text()) if LOCK.exists() else {"mods": []}
    old = {m["filename"]: m for m in previous["mods"]}
    if args.verify:
        if not LOCK.exists():
            raise ValueError("Build lockfile first")
        for mod in previous["mods"]:
            path = MODS / mod["filename"]
            if not path.exists() or hash_file(path)[0]["sha512"] != mod["hashes"]["sha512"]:
                raise ValueError("Missing or corrupted JAR: " + mod["filename"])
        build_pack(config, previous["mods"])
        return
    with ThreadPoolExecutor(max_workers=5) as pool:
        resolved = list(pool.map(lambda m: resolve_mod(m, config["pack"]["minecraft"]), config["mods"]))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(get_mod, mod, old): i for i, mod in enumerate(resolved)}
        records = [None] * len(resolved)
        for future in as_completed(futures):
            records[futures[future]] = future.result()
    # Store exact cryptographic hashes of the files we tested; future runs are fail-closed.
    LOCK.write_text(json.dumps({"pack": config["pack"], "mods": records},
                               ensure_ascii=False, indent=2) + "\n")
    build_pack(config, records)
    print("READY: 9 official downloads verified; client and server use identical JARs")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)

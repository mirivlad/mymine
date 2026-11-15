#!/usr/bin/env python3
"""Build a reproducible Modrinth pack and a launcher download manifest.

No third-party mods, shaderpacks or resourcepacks are redistributed: the pack
pins HTTPS URLs and upstream SHA-512 checksums for client-side downloads.
"""
import argparse
import json
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
USER_AGENT = "MyMine/0.5 (+https://github.com/mirivlad/mymine)"
HEADERS = {"User-Agent": USER_AGENT}
BASE = "https://api.modrinth.com/v2/"


def fetch(path):
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=HEADERS), timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--mrpack", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads((HERE / "client-pack.json").read_text(encoding="utf-8"))
    game = config["game"]
    entries = list(config["entries"])
    files = []
    downloads = []
    visited = set()
    queue = list(entries)
    while queue:
        entry = queue.pop(0)
        version = fetch("version/" + urllib.parse.quote(entry["version"]))
        project = fetch("project/" + urllib.parse.quote(version["project_id"]))
        if version["project_id"] in visited:
            continue
        if game not in version["game_versions"]:
            raise ValueError(f'{project["title"]}: not compatible with {game}')
        expected_loader = {"mods": "fabric", "shaderpacks": "iris", "resourcepacks": "minecraft"}[entry["type"]]
        if expected_loader not in version["loaders"]:
            raise ValueError(f'{project["title"]}: missing expected loader {expected_loader}')
        if version["version_type"] != "release":
            raise ValueError(f'{project["title"]}: selected non-release version {version["version_number"]}')
        upstream_file = next((item for item in version["files"] if item.get("primary")), version["files"][0])
        filename = upstream_file["filename"]
        if "/" in filename or "\\" in filename or filename in (".", "..") or "\t" in filename:
            raise ValueError("Unsafe filename: " + filename)
        url = upstream_file["url"]
        if not url.startswith("https://cdn.modrinth.com/"):
            raise ValueError("Unexpected upstream CDN: " + url)
        digest = upstream_file["hashes"]["sha512"]
        path = entry["type"] + "/" + filename
        if not path.endswith((".jar", ".zip")):
            raise ValueError("Unsupported file: " + path)

        downloads.append("\t".join([entry["type"], filename, url, digest]))
        files.append({
            "path": path,
            "hashes": {"sha512": digest},
            "env": {"client": "required", "server": "unsupported"},
            "downloads": [url],
            "fileSize": upstream_file["size"]
        })
        visited.add(version["project_id"])
        print(f'{entry["type"]}: {project["title"]} {version["version_number"]} ({filename})', flush=True)

        for dep in version.get("dependencies", []):
            if dep.get("dependency_type") != "required":
                continue
            dep_project_id = dep.get("project_id")
            if not dep_project_id or dep_project_id in visited or any(
                q.get("project_id") == dep_project_id for q in queue
            ):
                continue
            if any(x.get("project") == dep_project_id for x in entries):
                continue
            if dep.get("version_id"):
                new_version_id = dep["version_id"]
            else:
                qs = urllib.parse.urlencode({
                    "game_versions": json.dumps([game], separators=(",", ":")),
                    "loaders": json.dumps(["fabric"], separators=(",", ":"))
                })
                candidates = fetch("project/" + dep_project_id + "/version?" + qs)
                stable = [v for v in candidates if v["version_type"] == "release"]
                if not stable:
                    raise ValueError(f"No stable Fabric dependency for {project['title']}: {dep_project_id}")
                new_version_id = stable[0]["id"]
            queue.append({"type": "mods", "project_id": dep_project_id, "version": new_version_id})

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        "# MyMine pinned downloads, version " + game + "\n" + "\n".join(downloads) + "\n",
        encoding="utf-8"
    )
    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": "MyMine-" + game,
        "name": config["name"],
        "summary": "Fabric performance mods, Iris shaders and optional resource packs. Upstream files are not bundled.",
        "files": files,
        "dependencies": {"minecraft": game, "fabric-loader": config["fabricLoader"]}
    }
    args.mrpack.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.mrpack, "w", compression=zipfile.ZIP_DEFLATED) as pack:
        pack.writestr("modrinth.index.json", json.dumps(index, indent=2, ensure_ascii=False))
        pack.writestr("overrides/MyMine-packs-README.txt",
                      "Shader packs and resource packs are installed but NOT enabled.\n"
                      "Choose one in Minecraft Video Settings > Shader Packs and Options > Resource Packs.\n"
                      "Default is vanilla visuals (safer for low-end computers).\n")
    print(f"Wrote {len(files)} client files to {args.mrpack}")


if __name__ == "__main__":
    main()

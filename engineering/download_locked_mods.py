#!/usr/bin/env python3
"""Fetch locked official mod JARs for Docker image build; fail closed."""
import hashlib
import json
import pathlib
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

def main(lock_file, out_dir):
    lock = json.loads(pathlib.Path(lock_file).read_text())
    mods = lock["mods"]
    if lock["pack"]["minecraft"] != "1.21.1" or len(mods) != 14:
        raise ValueError("Invalid Engineering mod lockfile")
    dest = pathlib.Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for entry in mods:
        if entry.get("side","both") == "client":
            continue
        fname = entry["filename"]
        url = entry["url"]
        split = urllib.parse.urlsplit(url)
        allowed_hosts = ("mediafilez.forgecdn.net", "cdn.modrinth.com")
        if split.scheme != "https" or split.hostname not in allowed_hosts:
            raise ValueError("Unexpected mod URL " + url)
        if fname != pathlib.PurePosixPath(fname).name or not fname.endswith(".jar"):
            raise ValueError("Unsafe mod filename")
        req = urllib.request.Request(url, headers={"User-Agent":"MyMine/Engineering-image"})
        with urllib.request.urlopen(req, timeout=75) as source:
            if urllib.parse.urlsplit(source.geturl()).hostname != split.hostname:
                raise ValueError("Untrusted mod download redirect")
            with (dest / fname).open("wb") as output:
                digest = hashlib.sha512()
                total = 0
                while (chunk := source.read(1024 * 1024)):
                    output.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
                    if total > 128 * 1024 * 1024:
                        raise ValueError("Oversized mod: " + fname)
        if digest.hexdigest() != entry["hashes"]["sha512"] or total != entry["fileSize"]:
            raise ValueError("Checksum mismatch " + fname)
        if not zipfile.is_zipfile(dest / fname):
            raise ValueError("Corrupt mod archive " + fname)
        print("Verified", fname, total, flush=True)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

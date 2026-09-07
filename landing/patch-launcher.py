#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

RESOURCE = "mymine-instance.properties"
EOCD = b"PK\x05\x06"


def prefix_length(data: bytes) -> int:
    eocd = data.rfind(EOCD)
    if eocd < 0 or eocd + 22 > len(data):
        raise SystemExit("not a supported ZIP/JAR artifact: EOCD not found")
    cd_size = struct.unpack_from("<I", data, eocd + 12)[0]
    cd_offset = struct.unpack_from("<I", data, eocd + 16)[0]
    prefix = eocd - cd_size - cd_offset
    if prefix < 0:
        raise SystemExit("invalid ZIP central directory offsets")
    return prefix


def patch(path: Path, properties: bytes) -> None:
    original = path.read_bytes()
    prefix_len = prefix_length(original)
    prefix = original[:prefix_len]
    mode = stat.S_IMODE(path.stat().st_mode)

    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    zip_tmp = tmp.with_suffix(tmp.suffix + ".zip")
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            zip_tmp, "w", allowZip64=True
        ) as target:
            for info in source.infolist():
                if info.filename == RESOURCE:
                    continue
                target.writestr(info, source.read(info.filename))
            target.writestr(RESOURCE, properties, compress_type=zipfile.ZIP_DEFLATED)

        with tmp.open("wb") as output:
            output.write(prefix)
            with zip_tmp.open("rb") as archive:
                while chunk := archive.read(1024 * 1024):
                    output.write(chunk)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
        zip_tmp.unlink(missing_ok=True)

    # Re-open after replacement so corruption is caught at container startup.
    with zipfile.ZipFile(path, "r") as verify:
        actual = verify.read(RESOURCE)
        if actual != properties:
            raise SystemExit(f"failed to inject {RESOURCE} into {path}")

    print(f"patched {path.name}: prefix={prefix_len} bytes")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} ARTIFACT PROPERTIES_FILE")
    patch(Path(sys.argv[1]), Path(sys.argv[2]).read_bytes())


if __name__ == "__main__":
    main()

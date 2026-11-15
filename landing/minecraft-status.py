#!/usr/bin/env python3
"""Read the Minecraft Java status protocol and maintain live landing metadata.

Uses the Compose service DNS name, not an external API, Docker socket, or
manually entered Minecraft version. A status failure retains the last version.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import socket
import struct
import sys
import tempfile
import time

DOCUMENT_ROOT = Path("/usr/share/nginx/html")
MAX_RESPONSE = 256 * 1024
VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z._+-]{0,40}$")


def varint(number: int) -> bytes:
    output = bytearray()
    while True:
        item = number & 0x7F
        number >>= 7
        output.append(item | (0x80 if number else 0))
        if not number:
            return bytes(output)


def read_exact(sock: socket.socket, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        portion = sock.recv(length - len(data))
        if not portion:
            raise EOFError("Minecraft server closed status connection")
        data.extend(portion)
    return bytes(data)


def read_varint(sock: socket.socket) -> int:
    result = 0
    for i in range(5):
        byte = read_exact(sock, 1)[0]
        result |= (byte & 0x7F) << (7 * i)
        if not byte & 0x80:
            return result
    raise ValueError("Overlong Minecraft VarInt")


def packet(payload: bytes) -> bytes:
    return varint(len(payload)) + payload


def query_version(host: str, port: int, timeout: float = 3.0) -> str:
    if not (1 <= port <= 65535):
        raise ValueError("Invalid Minecraft status port")
    host_bytes = host.encode("utf-8")
    if len(host_bytes) > 255:
        raise ValueError("Minecraft status host is too long")

    # Protocol 777 is a status handshake hint, not a login. Minecraft servers
    # answer status pings even when the client's protocol version is different.
    handshake = (
        varint(0)
        + varint(777)
        + varint(len(host_bytes)) + host_bytes
        + struct.pack(">H", port)
        + varint(1)
    )
    with socket.create_connection((host, port), timeout=timeout) as conn:
        conn.settimeout(timeout)
        conn.sendall(packet(handshake) + packet(varint(0)))
        frame_size = read_varint(conn)
        if not 1 <= frame_size <= MAX_RESPONSE:
            raise ValueError("Invalid Minecraft status frame size")
        response = read_exact(conn, frame_size)

    # Decode the packet within the size-bounded frame, without reading arbitrary
    # amounts of data from the remote server.
    index = 0

    def decode_int() -> int:
        nonlocal index
        value = 0
        for offset in range(5):
            if index >= len(response):
                raise EOFError("Incomplete Minecraft status packet")
            byte = response[index]
            index += 1
            value |= (byte & 0x7F) << (7 * offset)
            if not byte & 0x80:
                return value
        raise ValueError("Overlong status VarInt")

    if decode_int() != 0:
        raise ValueError("Expected Minecraft status response")
    size = decode_int()
    if not 1 <= size <= MAX_RESPONSE or index + size != len(response):
        raise ValueError("Invalid Minecraft status JSON length")
    parsed = json.loads(response[index:index + size].decode("utf-8"))
    raw = parsed["version"]["name"]
    if not isinstance(raw, str):
        raise ValueError("Minecraft status version is not text")

    version = raw.strip()
    if not VERSION_RE.fullmatch(version):
        match = re.search(r"(?:[0-9]+(?:\.[0-9]+){1,3}|[0-9]{2}w[0-9]{2}[a-z])", version)
        if match is None:
            raise ValueError("Minecraft status has no recognizable version")
        version = match.group()
    return version


def update_once(path: Path, host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    # Read and preserve all original instance metadata and the baked fallback.
    document = json.loads(path.read_text(encoding="utf-8"))
    old_version = document.get("version")
    if not isinstance(old_version, str) or not VERSION_RE.fullmatch(old_version):
        raise ValueError("Missing valid bundled Minecraft version")

    try:
        version = query_version(host, port, timeout=timeout)
    except (OSError, EOFError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        document["online"] = False
        state = (False, old_version)
        detail = type(error).__name__
    else:
        document["version"] = version
        document["online"] = True
        state = (True, version)
        detail = "live"

    document["lastChecked"] = int(time.time())
    data = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    # Atomic replacement keeps a concurrent nginx read from observing truncated
    # JSON; file is world-readable but contains only public server metadata.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".mymine-status-", delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fchmod(output.fileno(), 0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return state


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--once", action="store_true", help="Single status poll for tests")
    cli.add_argument("--file", type=Path, default=DOCUMENT_ROOT / "server.json")
    cli.add_argument("--host", default=os.environ.get("MYMINE_STATUS_HOST", "minecraft"))
    cli.add_argument("--port", type=int, default=int(os.environ.get("MYMINE_STATUS_PORT", "25565")))
    cli.add_argument("--interval", type=int, default=45)
    args = cli.parse_args()
    if not 1 <= args.port <= 65535 or not 5 <= args.interval <= 3600:
        cli.error("Invalid port or interval")

    previous = None
    while True:
        try:
            state = update_once(args.file, args.host, args.port)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"MyMine status: unable to update metadata: {error}", file=sys.stderr, flush=True)
            if args.once:
                return 1
        else:
            if state != previous:
                print(f"MyMine status: {'online' if state[0] else 'offline'}, "
                      f"version {state[1]}", flush=True)
            previous = state
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())

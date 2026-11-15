"""Tests for MyMine's live Minecraft Java status protocol."""
import importlib.util
import json
from pathlib import Path
import socketserver
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mymine_status", ROOT / "landing/minecraft-status.py")
STATUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATUS)


class TestServer(socketserver.TCPServer):
    allow_reuse_address = True


class StatusTests(unittest.TestCase):
    def fake_server(self, name):
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(2)
                self.request.recv(4096)
                body = json.dumps({"version": {"name": name}}).encode()
                result = STATUS.varint(0) + STATUS.varint(len(body)) + body
                self.request.sendall(STATUS.packet(result))
        server = TestServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_address[1]

    def test_server_protocol(self):
        port = self.fake_server("26.3")
        self.assertEqual(STATUS.query_version("127.0.0.1", port), "26.3")

    def test_modded_server_protocol(self):
        port = self.fake_server("Fabric 26.3")
        self.assertEqual(STATUS.query_version("127.0.0.1", port), "26.3")

    def test_live_version_updates_static_fallback(self):
        port = self.fake_server("26.3")
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "server.json"
            source = {"minecraft": "example.test:25565",
                      "auth": "https://auth.example.test/",
                      "version": "26.2", "template": "showcase"}
            path.write_text(json.dumps(source), encoding="utf-8")
            online, version = STATUS.update_once(path, "127.0.0.1", port)
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(online)
            self.assertEqual(version, "26.3")
            self.assertEqual(document["version"], "26.3")
            self.assertEqual(document["minecraft"], source["minecraft"])
            self.assertEqual(document["auth"], source["auth"])
            self.assertEqual(document["template"], source["template"])
            self.assertTrue(document["online"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)

    def test_unavailable_server_preserves_version(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "server.json"
            path.write_text(json.dumps({"version": "26.3"}), encoding="utf-8")
            online, version = STATUS.update_once(path, "127.0.0.1", 0)
            self.assertFalse(online)
            self.assertEqual(version, "26.3")
            self.assertFalse(json.loads(path.read_text())["online"])

    def test_untrusted_version_is_rejected(self):
        port = self.fake_server("<img src=x onerror=alert(1)>")
        with self.assertRaises(ValueError):
            STATUS.query_version("127.0.0.1", port)

    def test_all_templates_have_live_slots(self):
        for template in (ROOT / "landing/templates").glob("*.html.template"):
            with self.subTest(template=template.name):
                content = template.read_text(encoding="utf-8")
                self.assertIn("data-mymine-version", content)
                self.assertIn("/assets/mymine-live-version.js", content)
                self.assertIn("$" + "{MC_VERSION}", content)
                self.assertEqual(content.count("mymine-live-version.js"), 1)


if __name__ == "__main__":
    unittest.main()

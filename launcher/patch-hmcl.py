#!/usr/bin/env python3
from pathlib import Path
import os
import sys

root = Path(sys.argv[1])
auth_url = os.environ.get("MYMINE_AUTH_URL", "https://auth.mymine.mirv.top/")
if not auth_url.endswith("/"):
    auth_url += "/"

def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"patch target mismatch in {path}: {text.count(old)} matches")
    path.write_text(text.replace(old, new), encoding="utf-8")

account_list = root / "HMCL/src/main/java/org/jackhuang/hmcl/ui/account/AccountListPage.java"
replace_once(
    account_list,
    'System.getProperty("hmcl.offline.auth.restricted", "auto")',
    'System.getProperty("hmcl.offline.auth.restricted", "false")',
)
auth_servers = root / "HMCL/src/main/java/org/jackhuang/hmcl/setting/AuthlibInjectorServers.java"
old = '''        if (SettingsManager.isNewlyCreated() && Files.exists(configLocation)) {
            AuthlibInjectorServers configInstance;
            try {
                configInstance = JsonUtils.fromJsonFile(configLocation, AuthlibInjectorServers.class);
            } catch (IOException | JsonParseException e) {
                LOG.warning("Malformed authlib-injectors.json", e);
                return;
            }

            if (!configInstance.urls.isEmpty()) {'''
new = f'''        if (SettingsManager.isNewlyCreated()) {{
            AuthlibInjectorServers configInstance;
            if (Files.exists(configLocation)) {{
                try {{
                    configInstance = JsonUtils.fromJsonFile(configLocation, AuthlibInjectorServers.class);
                }} catch (IOException | JsonParseException e) {{
                    LOG.warning("Malformed authlib-injectors.json", e);
                    return;
                }}
            }} else {{
                configInstance = new AuthlibInjectorServers(List.of("{auth_url}"));
            }}

            if (!configInstance.urls.isEmpty()) {{'''
replace_once(auth_servers, old, new)
print(f"Patched HMCL for MyMine auth: {auth_url}")

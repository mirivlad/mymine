#!/usr/bin/env python3
from pathlib import Path
import os
import sys

root = Path(sys.argv[1])
auth_url = os.environ.get("MYMINE_AUTH_URL", "https://auth.mymine.mirv.top/")
if not auth_url.endswith("/"):
    auth_url += "/"


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"patch target mismatch in {path}: {count} matches, expected {expected}")
    path.write_text(text.replace(old, new), encoding="utf-8")


account_list = root / "HMCL/src/main/java/org/jackhuang/hmcl/ui/account/AccountListPage.java"
replace_exact(
    account_list,
    'System.getProperty("hmcl.offline.auth.restricted", "auto")',
    'System.getProperty("hmcl.offline.auth.restricted", "false")',
)

replace_exact(
    account_list,
    '''        public AccountListPageSkin(AccountListPage skinnable) {
            super(skinnable);

            {''',
    '''        public AccountListPageSkin(AccountListPage skinnable) {
            super(skinnable);

            skinnable.authServersProperty().removeIf(
                    server -> "https://littleskin.cn/api/yggdrasil/".equals(server.getUrl()));

            {''',
)

replace_exact(
    account_list,
    'boxMethods.getChildren().setAll(title, microsoftItem, wrapper);',
    'boxMethods.getChildren().setAll(title, wrapper);',
)
replace_exact(
    account_list,
    'boxMethods.getChildren().setAll(title, microsoftItem, offlineItem, boxAuthServers);',
    'boxMethods.getChildren().setAll(title, boxAuthServers, offlineItem);',
    expected=2,
)

replace_exact(
    account_list,
    '''                        ObservableValue<String> title = BindingMapping.of(server, AuthlibInjectorServer::getName);
                        item.titleProperty().bind(title);''',
    f'''                        ObservableValue<String> title;
                        if ("{auth_url}".equals(server.getUrl())) {{
                            item.setTitle("MyMine");
                            title = item.titleProperty();
                        }} else {{
                            title = BindingMapping.of(server, AuthlibInjectorServer::getName);
                            item.titleProperty().bind(title);
                        }}''',
)

default_servers = root / "HMCL/src/main/java/org/jackhuang/hmcl/setting/AuthlibInjectorServerList.java"
replace_exact(
    default_servers,
    '''    public static AuthlibInjectorServerList createDefault() {
        AuthlibInjectorServerList result = new AuthlibInjectorServerList();
        result.addLittleSkinIfAbsent();
        return result;
    }''',
    '''    public static AuthlibInjectorServerList createDefault() {
        return new AuthlibInjectorServerList();
    }''',
)

default_servers_test = root / "HMCL/src/test/java/org/jackhuang/hmcl/setting/AuthlibInjectorServerListTest.java"
replace_exact(
    default_servers_test,
    '''    /// Tests that newly created server lists contain LittleSkin by default.
    @Test
    public void defaultListContainsLittleSkin() {
        AuthlibInjectorServerList list = AuthlibInjectorServerList.createDefault();

        assertEquals(1, list.getServers().size());
        assertEquals(AuthlibInjectorServerList.LITTLE_SKIN_URL, list.getServers().get(0).getUrl());
    }''',
    '''    /// MyMine starts with no third-party authlib-injector providers.
    @Test
    public void defaultListContainsNoThirdPartyServers() {
        AuthlibInjectorServerList list = AuthlibInjectorServerList.createDefault();

        assertTrue(list.getServers().isEmpty());
    }''',
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
replace_exact(auth_servers, old, new)

print(f"Patched HMCL for MyMine auth: {auth_url}")
print("Microsoft hidden, LittleSkin removed, MyMine promoted to the first auth method")

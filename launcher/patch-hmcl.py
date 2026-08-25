#!/usr/bin/env python3
from pathlib import Path
import json
import os
import sys

root = Path(sys.argv[1])
auth_url = os.environ.get("MYMINE_AUTH_URL", "https://auth.mymine.mirv.top/")
server_name = os.environ.get("MYMINE_SERVER_NAME", "MyMine")
server_address = os.environ.get("MYMINE_SERVER_ADDRESS", "mymine.mirv.top:25565")
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
                        if (server.getUrl().equals("{auth_url}") || server.getUrl().startsWith("{auth_url}")) {{
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

# Add the MyMine server to Minecraft's multiplayer list once per game run directory.
# The marker deliberately makes this a migration rather than an advertisement that
# is forcibly re-added on every launch: if a player deletes MyMine later, it stays deleted.
game_launcher = root / "HMCL/src/main/java/org/jackhuang/hmcl/game/HMCLGameLauncher.java"
replace_exact(
    game_launcher,
    '''    public ManagedProcess launch() throws IOException, InterruptedException {
        generateOptionsTxt();
        return super.launch();
    }''',
    '''    public ManagedProcess launch() throws IOException, InterruptedException {
        generateOptionsTxt();
        MyMineServerList.ensure(repository.getRunDirectory(version.getId()));
        return super.launch();
    }''',
)
replace_exact(
    game_launcher,
    '''    public void makeLaunchScript(Path scriptFile) throws IOException {
        generateOptionsTxt();
        super.makeLaunchScript(scriptFile);
    }''',
    '''    public void makeLaunchScript(Path scriptFile) throws IOException {
        generateOptionsTxt();
        MyMineServerList.ensure(repository.getRunDirectory(version.getId()));
        super.makeLaunchScript(scriptFile);
    }''',
)

helper_source = '''/*
 * MyMine launcher patch.
 * Distributed under the same GPLv3 terms as HMCL.
 */
package org.jackhuang.hmcl.game;

import org.glavo.nbt.io.NBTCodec;
import org.glavo.nbt.tag.CompoundTag;
import org.glavo.nbt.tag.ListTag;
import org.glavo.nbt.tag.Tag;
import org.glavo.nbt.tag.TagType;
import org.jackhuang.hmcl.util.io.FileUtils;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Locale;

import static org.jackhuang.hmcl.util.logging.Logger.LOG;

/** Adds the official MyMine server to Minecraft's multiplayer list once. */
final class MyMineServerList {
    static final String SERVER_NAME = __SERVER_NAME__;
    static final String SERVER_ADDRESS = __SERVER_ADDRESS__;
    static final String MARKER_FILE = ".mymine-server-list-v1";

    private MyMineServerList() {
    }

    static void ensure(Path runDirectory) {
        Path marker = runDirectory.resolve(MARKER_FILE);
        if (Files.isRegularFile(marker)) {
            return;
        }

        Path serversFile = runDirectory.resolve("servers.dat");
        try {
            Files.createDirectories(runDirectory);

            CompoundTag root;
            ListTag<CompoundTag> servers;
            boolean changed = false;

            if (Files.isRegularFile(serversFile)) {
                root = NBTCodec.of().readTag(serversFile, TagType.COMPOUND);
                Tag serversTag = root.get("servers");
                if (serversTag == null) {
                    servers = new ListTag<>(TagType.COMPOUND);
                    root.addTag("servers", servers);
                    changed = true;
                } else if (serversTag instanceof ListTag<?> rawServers
                        && (rawServers.isEmpty() || rawServers.getElementType() == TagType.COMPOUND)) {
                    @SuppressWarnings("unchecked")
                    ListTag<CompoundTag> castServers = (ListTag<CompoundTag>) rawServers;
                    servers = castServers;
                } else {
                    LOG.warning("Not modifying malformed Minecraft server list: " + serversFile);
                    return;
                }
            } else {
                root = new CompoundTag();
                servers = new ListTag<>(TagType.COMPOUND);
                root.addTag("servers", servers);
                changed = true;
            }

            if (!containsAddress(servers, SERVER_ADDRESS)) {
                ListTag<CompoundTag> merged = new ListTag<>(TagType.COMPOUND);
                merged.addTag(new CompoundTag()
                        .addString("name", SERVER_NAME)
                        .addString("ip", SERVER_ADDRESS));
                for (CompoundTag server : servers) {
                    merged.addTag(server.clone());
                }
                root.addTag("servers", merged);
                changed = true;
            }

            if (changed) {
                FileUtils.saveSafely(serversFile, output -> NBTCodec.of().writeTag(output, root));
            }

            Files.writeString(marker, SERVER_ADDRESS, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING,
                    StandardOpenOption.WRITE);
        } catch (Exception e) {
            // A broken/locked servers.dat must never prevent Minecraft from starting.
            LOG.warning("Failed to add MyMine to Minecraft multiplayer list", e);
        }
    }

    private static boolean containsAddress(ListTag<CompoundTag> servers, String address) {
        String target = normalizeAddress(address);
        for (CompoundTag server : servers) {
            if (target.equals(normalizeAddress(server.getStringOrDefault("ip", "")))) {
                return true;
            }
        }
        return false;
    }

    static String normalizeAddress(String address) {
        String normalized = address.trim().toLowerCase(Locale.ROOT);
        if (!normalized.isEmpty() && normalized.indexOf(':') < 0) {
            normalized += ":25565";
        }
        return normalized;
    }
}
'''
helper_source = helper_source.replace("__SERVER_NAME__", json.dumps(server_name))
helper_source = helper_source.replace("__SERVER_ADDRESS__", json.dumps(server_address))
helper = root / "HMCL/src/main/java/org/jackhuang/hmcl/game/MyMineServerList.java"
helper.write_text(helper_source, encoding="utf-8")

test_source = '''/*
 * MyMine launcher patch tests.
 * Distributed under the same GPLv3 terms as HMCL.
 */
package org.jackhuang.hmcl.game;

import org.glavo.nbt.io.NBTCodec;
import org.glavo.nbt.tag.CompoundTag;
import org.glavo.nbt.tag.ListTag;
import org.glavo.nbt.tag.TagType;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class MyMineServerListTest {
    @TempDir
    Path tempDir;

    @Test
    void addsMyMineFirstAndPreservesExistingServers() throws IOException {
        writeServers(new CompoundTag()
                .addString("name", "Existing")
                .addString("ip", "example.org:25565"));

        MyMineServerList.ensure(tempDir);

        ListTag<CompoundTag> servers = readServers();
        assertEquals(2, servers.size());
        assertEquals(MyMineServerList.SERVER_NAME, servers.getTag(0).getString("name"));
        assertEquals(MyMineServerList.SERVER_ADDRESS, servers.getTag(0).getString("ip"));
        assertEquals("Existing", servers.getTag(1).getString("name"));
        assertEquals("example.org:25565", servers.getTag(1).getString("ip"));
        assertTrue(Files.isRegularFile(tempDir.resolve(MyMineServerList.MARKER_FILE)));
    }

    @Test
    void doesNotDuplicateAnExistingDefaultPortAddress() throws IOException {
        String address = MyMineServerList.SERVER_ADDRESS;
        String equivalent = address.endsWith(":25565")
                ? address.substring(0, address.length() - ":25565".length())
                : address;
        writeServers(new CompoundTag()
                .addString("name", "Already here")
                .addString("ip", equivalent));

        MyMineServerList.ensure(tempDir);

        ListTag<CompoundTag> servers = readServers();
        assertEquals(1, servers.size());
        assertEquals("Already here", servers.getTag(0).getString("name"));
    }

    @Test
    void respectsDeletionAfterInitialMigration() throws IOException {
        MyMineServerList.ensure(tempDir);
        writeServers();

        MyMineServerList.ensure(tempDir);

        assertTrue(readServers().isEmpty());
    }

    private void writeServers(CompoundTag... entries) throws IOException {
        CompoundTag root = new CompoundTag();
        ListTag<CompoundTag> servers = new ListTag<>(TagType.COMPOUND);
        for (CompoundTag entry : entries) {
            servers.addTag(entry);
        }
        root.addTag("servers", servers);
        try (OutputStream output = Files.newOutputStream(tempDir.resolve("servers.dat"))) {
            NBTCodec.of().writeTag(output, root);
        }
    }

    private ListTag<CompoundTag> readServers() throws IOException {
        CompoundTag root = NBTCodec.of().readTag(tempDir.resolve("servers.dat"), TagType.COMPOUND);
        @SuppressWarnings("unchecked")
        ListTag<CompoundTag> servers = (ListTag<CompoundTag>) root.get("servers");
        return servers;
    }
}
'''
test = root / "HMCL/src/test/java/org/jackhuang/hmcl/game/MyMineServerListTest.java"
test.parent.mkdir(parents=True, exist_ok=True)
test.write_text(test_source, encoding="utf-8")

print(f"Patched HMCL for MyMine auth: {auth_url}")
print(f"MyMine multiplayer server: {server_name} ({server_address})")
print("Microsoft hidden, LittleSkin removed, MyMine promoted to the first auth method")

/*
 * MyMine automatic client assets (GPL-3.0).
 * The launcher only downloads pinned upstream files; it never redistributes them.
 */
package org.jackhuang.hmcl.game;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

import static org.jackhuang.hmcl.util.logging.Logger.LOG;

/** Installs 26.3 client-side mods plus selectable shaders and resource packs. */
final class MyMineClientPacks {
    static final String MARKER = ".mymine-26.3-client-pack-v1";
    private static final String MANIFEST = "/mymine-client-files.tsv";
    private static final long MAX_FILE = 128L * 1024 * 1024;
    private static final List<String> FOLDERS = List.of("mods", "shaderpacks", "resourcepacks");

    private MyMineClientPacks() {
    }

    private record Entry(String folder, String file, String url, String sha512) {
        Path destination(Path runDirectory) {
            return runDirectory.resolve(folder).resolve(file);
        }
    }

    static void ensure(Path runDirectory) {
        if ("false".equalsIgnoreCase(System.getProperty("mymine.client.packs", "true"))) {
            return;
        }
        Path marker = runDirectory.resolve(MARKER);
        if (Files.isRegularFile(marker)) {
            return;
        }
        Path staged = runDirectory.resolve(".mymine-client-pack-stage");
        List<Path> temporaryFiles = new ArrayList<>();
        try {
            List<Entry> entries = loadEntries();
            Files.createDirectories(staged);
            for (Entry entry : entries) {
                Path destination = entry.destination(runDirectory);
                if (Files.exists(destination)) {
                    if (!hashMatches(destination, entry.sha512)) {
                        // Never replace mods or resources that the player installed.
                        throw new IOException("Conflicting user file " + destination);
                    }
                    continue;
                }
                Path temp = staged.resolve(entry.file);
                download(entry.url, temp);
                temporaryFiles.add(temp);
                if (!hashMatches(temp, entry.sha512)) {
                    throw new IOException("SHA-512 mismatch for " + entry.file);
                }
            }
            for (Entry entry : entries) {
                Path destination = entry.destination(runDirectory);
                if (Files.exists(destination)) {
                    continue;
                }
                Files.createDirectories(destination.getParent());
                Path temp = staged.resolve(entry.file);
                try {
                    Files.move(temp, destination, StandardCopyOption.ATOMIC_MOVE);
                } catch (AtomicMoveNotSupportedException e) {
                    Files.move(temp, destination);
                }
            }
            Files.writeString(marker, "MyMine 26.3 client packs v1\n", StandardCharsets.UTF_8);
            LOG.info("MyMine client mods, shaderpacks and resourcepacks are available.");
        } catch (Exception e) {
            // Never prevent normal Minecraft launch because optional assets failed.
            LOG.warning("MyMine client packs could not be downloaded; launch continues", e);
        } finally {
            for (Path path : temporaryFiles) {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException e) {
                    LOG.warning("Cannot remove temporary MyMine client download " + path, e);
                }
            }
            try {
                Files.deleteIfExists(staged);
            } catch (IOException ignored) {
                // Safe to retry downloading on the next launch.
            }
        }
    }

    private static List<Entry> loadEntries() throws IOException {
        try (InputStream input = MyMineClientPacks.class.getResourceAsStream(MANIFEST)) {
            if (input == null) {
                throw new IOException("Missing bundled " + MANIFEST);
            }
            String manifest = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            List<Entry> entries = new ArrayList<>();
            for (String line : manifest.split("\\R")) {
                if (line.isBlank() || line.startsWith("#")) {
                    continue;
                }
                String[] fields = line.split("\\t", -1);
                if (fields.length != 4 || !FOLDERS.contains(fields[0])) {
                    throw new IOException("Invalid MyMine manifest line: " + line);
                }
                String file = fields[1];
                if (file.isBlank() || file.contains("/") || file.contains("\\") || file.equals("..")
                        || file.equals(".") || !file.endsWith(".jar") && !file.endsWith(".zip")) {
                    throw new IOException("Unsafe MyMine filename " + file);
                }
                URI uri = URI.create(fields[2]);
                if (!"https".equals(uri.getScheme()) || !"cdn.modrinth.com".equals(uri.getHost())) {
                    throw new IOException("Unexpected MyMine download URL " + uri);
                }
                if (!fields[3].matches("[a-fA-F0-9]{128}")) {
                    throw new IOException("Invalid SHA-512 for " + file);
                }
                entries.add(new Entry(fields[0], file, fields[2], fields[3]));
            }
            if (entries.isEmpty()) {
                throw new IOException("Empty MyMine client pack");
            }
            return entries;
        }
    }

    private static void download(String url, Path target) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) URI.create(url).toURL().openConnection();
        connection.setConnectTimeout(8_000);
        connection.setReadTimeout(20_000);
        connection.setInstanceFollowRedirects(false);
        try {
            if (connection.getResponseCode() != 200) {
                throw new IOException("Download HTTP " + connection.getResponseCode() + " for " + target.getFileName());
            }
            try (InputStream input = connection.getInputStream();
                 var output = Files.newOutputStream(target)) {
                byte[] buffer = new byte[64 * 1024];
                int size;
                long total = 0;
                while ((size = input.read(buffer)) != -1) {
                    total += size;
                    if (total > MAX_FILE) {
                        throw new IOException("MyMine download too large: " + target);
                    }
                    output.write(buffer, 0, size);
                }
            }
        } finally {
            connection.disconnect();
        }
    }

    private static boolean hashMatches(Path file, String expected) throws IOException {
        final MessageDigest sha;
        try {
            sha = MessageDigest.getInstance("SHA-512");
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
        try (InputStream input = Files.newInputStream(file)) {
            byte[] buffer = new byte[64 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) {
                sha.update(buffer, 0, read);
            }
        }
        return HexFormat.of().formatHex(sha.digest()).equalsIgnoreCase(expected);
    }
}

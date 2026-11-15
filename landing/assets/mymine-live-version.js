/* Update only Minecraft version labels using the server's live status response.
   The bundled version remains visible when the game server is offline. */
(() => {
  const nodes = Array.from(document.querySelectorAll("[data-mymine-version]"));
  const buildVersion = nodes.length ? nodes[0].textContent.trim() : "";
  let shownTitleVersion = buildVersion;

  function validVersion(value) {
    return typeof value === "string" && /^[0-9][0-9A-Za-z._+-]{0,40}$/.test(value);
  }

  async function refreshVersion() {
    try {
      const response = await fetch("/server.json", { cache: "no-store" });
      if (!response.ok) return;
      const status = await response.json();
      if (!validVersion(status.version)) return;
      const version = status.version;
      nodes.forEach((node) => {
        node.textContent = version;
        node.dataset.source = status.online === true ? "server" : "image";
        node.title = status.online === true
          ? "Версия запущенного Minecraft-сервера"
          : "Последняя известная версия Minecraft; сервер сейчас недоступен";
      });
      if (shownTitleVersion && shownTitleVersion !== version) {
        document.title = document.title.replace(shownTitleVersion, version);
      }
      shownTitleVersion = version;
    } catch (_) {
      // Preserve bundled text when the landing status endpoint is unavailable.
    }
  }

  void refreshVersion();
  window.setInterval(refreshVersion, 45000);
})();

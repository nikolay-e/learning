"use strict";

// Installable, and readable with no network: the whole reference is static text and code.
// A rebuilt page reaches an open tab by itself — a reader is never mid-action here, so a
// fresh worker is applied the moment it lands.
(() => {
  if (!("serviceWorker" in navigator)) return;

  const POLL_MS = 15 * 60 * 1000;
  const buildId =
    document
      .querySelector('meta[name="app-version"]')
      ?.getAttribute("content") || "dev";
  const hadController = Boolean(navigator.serviceWorker.controller);
  let reloading = false;

  navigator.serviceWorker
    // The build id rides on the URL: without it the browser would compare byte-identical
    // worker scripts across builds and never install the new shell.
    .register(`sw.js?v=${encodeURIComponent(buildId)}`, { scope: "./" })
    .then((registration) => {
      const apply = (worker) => worker.postMessage({ type: "SKIP_WAITING" });
      if (registration.waiting && hadController) apply(registration.waiting);
      registration.addEventListener("updatefound", () => {
        const fresh = registration.installing;
        if (!fresh || !hadController) return;
        fresh.addEventListener("statechange", () => {
          if (fresh.state === "installed") apply(fresh);
        });
      });

      const checkForUpdate = () => registration.update().catch(() => {});
      setInterval(checkForUpdate, POLL_MS);
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") checkForUpdate();
      });
    })
    .catch(() => {});

  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (reloading || !hadController) return;
    reloading = true;
    location.reload();
  });
})();

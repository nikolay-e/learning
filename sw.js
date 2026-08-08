// GitHub Pages serves this repo under /learning/, so every path here is relative to that
// scope. The version arrives as ?v=<build id> on the registration URL: a new build asks for a
// worker URL the browser has never seen, which is what makes it install at all.
const VERSION = new URL(self.location).searchParams.get("v") || "dev";
const SHELL = `learning-shell-${VERSION}`;

const SHELL_FILES = [
  "./",
  "./index.html",
  "./assets/style.css",
  "./assets/app.js",
  "./assets/highlight.min.js",
  "./assets/hljs-protobuf.min.js",
  "./manifest.webmanifest",
  "./assets/icons/learning-icon-192.png",
  "./assets/icons/learning-icon-512.png",
  "./assets/icons/learning-icon-512-maskable.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((cache) => cache.addAll(SHELL_FILES)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  if (new URL(request.url).origin !== self.location.origin) return;

  // The page comes from the network first, so a rebuilt reference is never held back by a
  // cache; the cache is what makes the whole thing readable on a plane.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() =>
          caches
            .match(request)
            .then((hit) => hit ?? caches.match("./index.html").then((shell) => shell ?? Response.error())),
        ),
    );
    return;
  }

  event.respondWith(
    caches.match(request).then(
      (hit) =>
        hit ??
        fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(SHELL).then((cache) => cache.put(request, copy));
          }
          return response;
        }),
    ),
  );
});

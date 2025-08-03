const CACHE_NAME = "beach-volley-cache-v1";
const FILES_TO_CACHE = [
  "/",
  "/login",
  "/register",
  "/static/style.css",
  "/static/stylepagine.css",
  "/static/script.js",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/img0.png",
  "/static/img1.png",
  "/static/manifest.json"
];

self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(FILES_TO_CACHE))
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", e => {
  e.respondWith(
    caches.match(e.request).then(response => response || fetch(e.request))
  );
});

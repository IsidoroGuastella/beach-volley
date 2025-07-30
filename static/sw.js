self.addEventListener("install", e => {
  e.waitUntil(
    caches.open("beach-volley-cache").then(cache => {
      return cache.addAll([
        "/static/style.css",
        "/static/script.js",
        "/static/icon-192.png",
        "/static/icon-512.png",
        "/static/manifest.json",
        "/"
      ]);
    })
  );
});

self.addEventListener("fetch", e => {
  e.respondWith(
    caches.match(e.request).then(response => response || fetch(e.request))
  );
});

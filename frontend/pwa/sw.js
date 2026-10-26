// =========================================================
// OpenLane service worker
// - Pages: always try the network first (so data is fresh),
//   show the offline page when there is no connection.
// - CSS / JS / icons: network first, cached copy when offline.
// - /api/ requests and form posts are never cached
//   (they hold personal data and must always be live).
// Bump VERSION when you change this file.
// =========================================================

const VERSION = "openlane-v1";
const OFFLINE_URL = "/offline";
const PRECACHE = [
    OFFLINE_URL,
    "/css/styles.css",
    "/js/pwa.js",
    "/icons/icon-192.png",
    "/icons/icon-512.png",
    "/manifest.webmanifest",
];

self.addEventListener("install", event => {
    event.waitUntil(caches.open(VERSION).then(cache => cache.addAll(PRECACHE)));
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    // Remove caches from older versions
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(key => key !== VERSION).map(key => caches.delete(key))))
            .then(() => self.clients.claim())
    );
});

function isStaticAsset(url) {
    return url.pathname.startsWith("/css/") || url.pathname.startsWith("/js/") || url.pathname.startsWith("/icons/");
}

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    // Only handle GET requests from our own site, never the API
    if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request).catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }

    if (isStaticAsset(url)) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    if (response.ok) {
                        const copy = response.clone();
                        caches.open(VERSION).then(cache => cache.put(request, copy));
                    }
                    return response;
                })
                .catch(() => caches.match(request))
        );
    }
});

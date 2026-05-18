/**
 * CitizenTest PWA Service Worker
 * Caches main pages and static assets for offline / Add to Home Screen.
 */
// Bump this to force clients to refresh cached HTML/assets.
const CACHE_NAME = 'citizentest-v8';
const URLS = [
  // Keep only critical static assets for offline; do NOT precache HTML routes
  // because we want main pages to update immediately.
  '/static/styles.css',
  '/static/images/logo.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(URLS).catch(function () {
        // Ignore if some URLs fail (e.g. offline)
      });
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== CACHE_NAME; }).map(function (k) { return caches.delete(k); })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function (event) {
  var url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (event.request.method !== 'GET') return;

  // Never cache HTML/doc navigations; always go to network first
  // so UI changes (like removing "My Journey") are reflected instantly.
  if (event.request.mode === 'navigate' || (event.request.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(
      fetch(event.request).catch(function () {
        return caches.match('/static/images/logo.png').then(function () {
          return Response.error();
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function (cached) {
      if (cached) return cached;
      return fetch(event.request)
        .then(function (res) {
          if (!res || res.status !== 200 || res.type !== 'basic') return res;
          var clone = res.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(event.request, clone);
          });
          return res;
        })
        .catch(function () {
          return caches.match('/').then(function (fallback) {
            return fallback || Response.error();
          });
        });
    })
  );
});

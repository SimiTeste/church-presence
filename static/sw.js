self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('ebd-presenca-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/icon-192.png',
        '/static/icon-512.png'
      ]);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
const CACHE = 'bjorklund-poker-v3';
const CORE = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './images/loga_bjorklund.png',
  './images/splash.mp4',
  './images/splash.webm',
  // Bakåtkompatibilitet om någon råkat lägga filerna i "image/"
  './image/splash.mp4',
  './image/splash.webm',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      for (const u of CORE) {
        try {
          await cache.add(u);
        } catch (_) {
          /* t.ex. fel sökväg vid lokal öppning */
        }
      }
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      // Vissa webbläsare gör Range-requests för video. Matcha då på URL istället.
      return caches.match(e.request.url).then((cached2) => cached2 || fetch(e.request).catch(() => cached2));
    })
  );
});

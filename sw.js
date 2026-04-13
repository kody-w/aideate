// AIdeate Service Worker — offline-first PWA support
const CACHE_VERSION = 'aideate-v6';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './templates.js',
  './samples/example-workshop.json',
  './templates/general.json',
  './templates/b2b-sales.json',
  './templates/b2c-sales.json',
  './templates/healthcare.json',
  './templates/financial-services.json',
  './templates/manufacturing.json',
  './templates/energy.json',
  './templates/federal-government.json',
  './templates/slg-government.json',
  './templates/professional-services.json',
  './templates/retail-cpg.json',
  './templates/software-digital.json',
  './templates/human-resources.json',
  './templates/it-management.json'
];

// Install: pre-cache all app files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: stale-while-revalidate for HTML, cache-first for other assets
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  const isHTML = event.request.destination === 'document' ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('/');

  if (isHTML) {
    // Stale-while-revalidate: serve cache immediately, update in background
    event.respondWith(
      caches.open(CACHE_VERSION).then(cache =>
        cache.match(event.request).then(cached => {
          const networkFetch = fetch(event.request).then(response => {
            if (response.ok) cache.put(event.request, response.clone());
            return response;
          }).catch(() => cached);

          return cached || networkFetch;
        })
      )
    );
  } else {
    // Cache-first for static assets
    event.respondWith(
      caches.match(event.request).then(cached =>
        cached || fetch(event.request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_VERSION).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
      )
    );
  }
});

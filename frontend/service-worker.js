const CACHE_NAME = 'danfez-lift-v2.0.1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/login.html',
  '/register.html',
  '/forgot-password.html',
  '/reset-password.html',
  '/verify-email.html',
  '/dashboard.html',
  '/lifts.html',
  '/simulator.html',
  '/maintenance.html',
  '/alerts.html',
  '/technicians.html',
  '/reports.html',
  '/users.html',
  '/settings.html',
  '/profile.html',
  '/offline.html',
  '/manifest.json',
  '/assets/css/danfez-theme.css',
  '/assets/js/api.js',
  '/assets/js/auth.js',
  '/assets/js/app.js',
  '/assets/js/pwa.js',
  '/assets/icons/danfez-logo.svg',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Danfez ServiceWorker] Caching static shell');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Danfez ServiceWorker] Non-critical cache error:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Danfez ServiceWorker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // NEVER cache API requests or WebSocket connections (pass through to native network)
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws')) {
    return;
  }

  // Network-first with cache fallback for HTML pages, cache-first for static assets
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || caches.match('/offline.html');
          });
        })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return cachedResponse || fetch(event.request).then((response) => {
          return response;
        });
      }).catch(() => {
        if (event.request.destination === 'document') {
          return caches.match('/offline.html');
        }
      })
    );
  }
});

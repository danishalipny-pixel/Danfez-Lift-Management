/**
 * DANFEZ TECH HOUSE — Progressive Web App Controller
 */

let deferredPrompt = null;

// Register & Update Service Worker immediately
const isLocalhost = window.location.hostname === 'localhost' ||
                    window.location.hostname === '127.0.0.1' ||
                    window.location.hostname === '0.0.0.0';

if ('serviceWorker' in navigator) {
  if (isLocalhost) {
    // On localhost, immediately unregister any existing service worker to prevent stale 503 intercepts
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((reg) => {
        reg.unregister();
        console.log('[Danfez PWA] Unregistered service worker on localhost');
      });
    });
  } else {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('service-worker.js?v=2.0.4')
        .then((reg) => {
          reg.update();
          console.log('[Danfez PWA] Service Worker registered and updated:', reg.scope);
        })
        .catch((err) => {
          console.warn('[Danfez PWA] Service Worker registration failed:', err);
        });
    });
  }
}

// Automatically clear legacy caches from client storage
if ('caches' in window) {
  caches.keys().then((names) => {
    names.forEach((name) => {
      if (isLocalhost || name !== 'danfez-lift-v2.0.4') {
        console.log('[Danfez PWA] Removing outdated cache:', name);
        caches.delete(name);
      }
    });
  });
}

// Intercept Install Prompt
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('[Danfez PWA] Install prompt captured');
  
  const installBtn = document.getElementById('pwa-install-btn');
  if (installBtn) {
    installBtn.classList.remove('d-none');
    installBtn.addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        console.log(`[Danfez PWA] User install choice: ${outcome}`);
        deferredPrompt = null;
        installBtn.classList.add('d-none');
      }
    });
  }
});

// Network connection indicator sync
function updateOnlineStatus() {
  const badge = document.querySelector('.live-badge');
  if (!badge) return;

  if (navigator.onLine) {
    badge.className = 'live-badge online';
    badge.innerHTML = '<span class="pulse-dot"></span> LIVE / SIMULATION';
  } else {
    badge.className = 'live-badge offline';
    badge.innerHTML = '<i class="bi bi-wifi-off me-1"></i> SIMULATION / OFFLINE';
  }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
document.addEventListener('DOMContentLoaded', updateOnlineStatus);

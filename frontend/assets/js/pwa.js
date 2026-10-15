/**
 * DANFEZ TECH HOUSE — Progressive Web App Controller
 */

let deferredPrompt = null;

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((reg) => {
        console.log('[Danfez PWA] Service Worker registered with scope:', reg.scope);
      })
      .catch((err) => {
        console.warn('[Danfez PWA] Service Worker registration failed:', err);
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
    badge.innerHTML = '<i class="bi bi-wifi-off me-1"></i> OFFLINE';
    if (typeof showToast === 'function') {
      showToast('Network Disconnected', 'Operating in offline cache mode. Elevator commands require active connectivity.', 'warning');
    }
  }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);
document.addEventListener('DOMContentLoaded', updateOnlineStatus);

/**
 * DANFEZ TECH HOUSE — Smart Lift Management System
 * Shared App Shell, UI Components, and Audio Synthesizer
 */

class DanfezAudio {
  constructor() {
    this.ctx = null;
    this.soundEnabled = localStorage.getItem('danfez_sound_enabled') !== 'false';
  }

  initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  toggleSound(enabled) {
    this.soundEnabled = enabled;
    localStorage.setItem('danfez_sound_enabled', enabled ? 'true' : 'false');
  }

  // Dual tone ding-dong elevator arrival chime
  playArrivalChime() {
    if (!this.soundEnabled) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      // Tone 1: 587.33 Hz (D5)
      const osc1 = this.ctx.createOscillator();
      const gain1 = this.ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now);
      gain1.gain.setValueAtTime(0.2, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
      osc1.connect(gain1);
      gain1.connect(this.ctx.destination);
      osc1.start(now);
      osc1.stop(now + 0.6);

      // Tone 2: 440 Hz (A4)
      const osc2 = this.ctx.createOscillator();
      const gain2 = this.ctx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(440.00, now + 0.25);
      gain2.gain.setValueAtTime(0.22, now + 0.25);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.1);
      osc2.connect(gain2);
      gain2.connect(this.ctx.destination);
      osc2.start(now + 0.25);
      osc2.stop(now + 1.1);
    } catch (e) {
      // Audio context might be restricted before user interaction
    }
  }

  // Button click beep
  playButtonBeep() {
    if (!this.soundEnabled) return;
    try {
      this.initContext();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(880, now);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.1);
    } catch (e) {}
  }

  // Emergency stop warning buzz
  playWarningAlarm() {
    if (!this.soundEnabled) return;
    try {
      this.initContext();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(320, now);
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(now);
      osc.stop(now + 0.4);
    } catch (e) {}
  }
}

window.danfezAudio = new DanfezAudio();

// UI Toast Generator
function showToast(title, message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toastId = `toast-${Date.now()}`;
  let icon = 'bi-info-circle-fill text-primary';
  let headerClass = '';

  if (type === 'success') {
    icon = 'bi-check-circle-fill text-success';
  } else if (type === 'danger' || type === 'error') {
    icon = 'bi-exclamation-triangle-fill text-danger';
  } else if (type === 'warning') {
    icon = 'bi-exclamation-circle-fill text-warning';
  }

  const html = `
    <div id="${toastId}" class="toast align-items-center show shadow-lg border-0 mb-2 rounded-3" role="alert" aria-live="assertive" aria-atomic="true" style="min-width: 280px;">
      <div class="toast-header border-bottom-0 pb-1">
        <i class="bi ${icon} me-2 fs-6"></i>
        <strong class="me-auto text-navy small">${title}</strong>
        <small class="text-muted">just now</small>
        <button type="button" class="btn-close ms-2 mb-1" data-bs-dismiss="toast" aria-label="Close" onclick="document.getElementById('${toastId}').remove()"></button>
      </div>
      <div class="toast-body pt-0 pb-2 text-secondary small">
        ${message}
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', html);

  setTimeout(() => {
    const el = document.getElementById(toastId);
    if (el) el.remove();
  }, 4500);
}

// Navigation & Layout Helper
function renderAppShell(activePage) {
  const user = window.DanfezAuth ? window.DanfezAuth.getUser() : null;
  const role = user ? user.role : 'viewer';
  const roleName = role ? role.toUpperCase() : 'GUEST';
  const userName = user ? user.full_name : 'Guest User';

  // Update mobile bottom nav active item
  document.querySelectorAll('.mobile-nav-item').forEach(el => {
    const pageAttr = el.getAttribute('data-page');
    if (pageAttr === activePage) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  // Highlight desktop sidebar link
  document.querySelectorAll('.danfez-sidebar .nav-link').forEach(el => {
    const href = el.getAttribute('href');
    if (href && href.includes(activePage)) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  // Toggle user-restricted navigation links (Admin only)
  if (role !== 'admin') {
    document.querySelectorAll('.admin-only').forEach(el => {
      el.style.display = 'none';
    });
  }

  // Populate user display
  const userNameEl = document.getElementById('user-display-name');
  if (userNameEl) userNameEl.textContent = userName;
  
  const userRoleEl = document.getElementById('user-display-role');
  if (userRoleEl) userRoleEl.textContent = roleName;

  // Setup Sidebar Toggle for mobile
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebar = document.querySelector('.danfez-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    });
  }

  // Setup notification bell
  updateAlertsBadge();
}

async function updateAlertsBadge() {
  const badge = document.getElementById('topbar-alert-count');
  if (!badge) return;
  try {
    const faults = await window.danfezApi.getFaults({ is_resolved: false });
    const count = faults.length;
    if (count > 0) {
      badge.textContent = count;
      badge.classList.remove('d-none');
    } else {
      badge.classList.add('d-none');
    }
  } catch (e) {}
}

window.showToast = showToast;
window.renderAppShell = renderAppShell;
window.updateAlertsBadge = updateAlertsBadge;

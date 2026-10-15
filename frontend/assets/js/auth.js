/**
 * DANFEZ TECH HOUSE — Access Control & Auth Utilities
 */

const DanfezAuth = {
  getUser() {
    return window.danfezApi.getCurrentUser();
  },

  getToken() {
    return window.danfezApi.getToken();
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  getUserRole() {
    const u = this.getUser();
    return u ? u.role : null;
  },

  isAdmin() {
    return this.getUserRole() === 'admin';
  },

  isTechnician() {
    const role = this.getUserRole();
    return role === 'technician' || role === 'admin';
  },

  isViewer() {
    return this.getUserRole() === 'viewer';
  },

  requireAuth(allowedRoles = null) {
    if (!this.isAuthenticated()) {
      window.danfezApi.ensureAdminSession();
    }
    return true;
  },

  async logout() {
    try {
      await window.danfezApi.logout();
    } catch (e) {
      window.danfezApi.clearSession();
    }
    window.location.href = '/dashboard.html';
  }
};

window.DanfezAuth = DanfezAuth;

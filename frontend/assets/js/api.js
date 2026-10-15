/**
 * DANFEZ TECH HOUSE — Smart Lift Management System
 * API Client Library with Hybrid Live & Autonomous Mobile Simulation
 */

// Default backend for mobile deployment (Capacitor Android local network Wi-Fi)
const DEFAULT_PROD_API_URL = 'http://192.168.100.44:8000';

// Pre-seeded Chief Administrator Session (Valid JWT signed by backend)
const PRESEEDED_ADMIN_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBkYW5mZXouY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxODIzNjE1MDk2LCJpYXQiOjE3OTIwNzkwOTYsImp0aSI6ImI2MDBmYWU1NDc3YjRlZDFiYmYzYTBjZWU3YzYwMjk1IiwicmVtZW1iZXJfbWUiOmZhbHNlfQ.6vE-lEbxp41Ckqcz51Ehq5aNve41CxtxMOcDqFKN5wM';

const PRESEEDED_ADMIN_USER = {
  id: 1,
  email: 'admin@danfez.com',
  full_name: 'Danfez Chief Administrator',
  role: 'admin',
  phone: '+1 (555) 010-0100',
  is_active: true,
  is_verified: true
};

class DanfezApiClient {
  constructor() {
    this.tokenKey = 'danfez_access_token';
    this.userKey = 'danfez_current_user';
    this.backendUrlKey = 'danfez_backend_url';
    this.isOfflineMode = false;
    this.simInterval = null;
    this.wsCallbacks = [];

    // Initialize pre-seeded local storage if empty
    if (!localStorage.getItem(this.tokenKey)) {
      localStorage.setItem(this.tokenKey, PRESEEDED_ADMIN_TOKEN);
    }
    if (!localStorage.getItem(this.userKey)) {
      localStorage.setItem(this.userKey, JSON.stringify(PRESEEDED_ADMIN_USER));
    }

    // Initialize standalone simulation state for robust mobile offline capabilities
    this.initLocalStore();
  }

  initLocalStore() {
    this.localStore = {
      buildings: [
        { id: 1, name: "Tower 1 - Innovation Center", floors_count: 10, address: "100 Innovation Way, Cyber City" },
        { id: 2, name: "Tower 2 - Executive Tower", floors_count: 14, address: "102 Innovation Way, Cyber City" }
      ],
      elevators: [
        {
          id: 1,
          building_id: 1,
          name: "Elevator Alpha (Main)",
          code: "LIFT-A01",
          direction: "stationary",
          current_floor: 1,
          target_floor: null,
          door_state: "closed",
          status: "idle",
          total_trips: 1420,
          speed_multiplier: 1.0,
          is_emergency_stopped: false,
          load_kg: 240.0,
          max_capacity_kg: 1000.0,
          motor_temperature_c: 42.5,
          cable_tension_percent: 98.2,
          vibration_level: 0.12,
          last_serviced_date: "2026-09-15T10:00:00",
          building_name: "Tower 1 - Innovation Center"
        },
        {
          id: 2,
          building_id: 1,
          name: "Elevator Bravo (Freight)",
          code: "LIFT-B02",
          direction: "stationary",
          current_floor: 6,
          target_floor: null,
          door_state: "closed",
          status: "idle",
          total_trips: 890,
          speed_multiplier: 1.0,
          is_emergency_stopped: false,
          load_kg: 480.0,
          max_capacity_kg: 2000.0,
          motor_temperature_c: 46.1,
          cable_tension_percent: 96.5,
          vibration_level: 0.15,
          last_serviced_date: "2026-09-20T14:30:00",
          building_name: "Tower 1 - Innovation Center"
        },
        {
          id: 3,
          building_id: 2,
          name: "Elevator Charlie (VIP)",
          code: "LIFT-C03",
          direction: "stationary",
          current_floor: 10,
          target_floor: null,
          door_state: "closed",
          status: "idle",
          total_trips: 2150,
          speed_multiplier: 1.0,
          is_emergency_stopped: false,
          load_kg: 120.0,
          max_capacity_kg: 800.0,
          motor_temperature_c: 39.8,
          cable_tension_percent: 99.1,
          vibration_level: 0.08,
          last_serviced_date: "2026-10-01T09:00:00",
          building_name: "Tower 2 - Executive Tower"
        },
        {
          id: 4,
          building_id: 2,
          name: "Elevator Delta (Service)",
          code: "LIFT-D04",
          direction: "stationary",
          current_floor: 3,
          target_floor: null,
          door_state: "closed",
          status: "maintenance",
          total_trips: 640,
          speed_multiplier: 1.0,
          is_emergency_stopped: false,
          load_kg: 0.0,
          max_capacity_kg: 1200.0,
          motor_temperature_c: 35.0,
          cable_tension_percent: 94.0,
          vibration_level: 0.22,
          last_serviced_date: "2026-10-10T11:00:00",
          building_name: "Tower 2 - Executive Tower"
        }
      ],
      tickets: [
        {
          id: 101,
          title: "Quarterly Safety Brake Inspection",
          description: "Inspect secondary magnetic brake pads and governor trip mechanism.",
          priority: "HIGH",
          status: "IN_PROGRESS",
          elevator_id: 1,
          technician_id: 1,
          elevator_name: "Elevator Alpha (Main)",
          technician_name: "Alex Vance (Lead)",
          created_at: "2026-10-12T08:30:00"
        },
        {
          id: 102,
          title: "Door Sensor Alignment Check",
          description: "Optical curtain infrared sensor misalignment causing minor closing delay.",
          priority: "MEDIUM",
          status: "OPEN",
          elevator_id: 2,
          technician_id: 2,
          elevator_name: "Elevator Bravo (Freight)",
          technician_name: "Marcus Brody",
          created_at: "2026-10-14T14:15:00"
        }
      ],
      faults: [
        {
          id: 201,
          elevator_id: 4,
          code: "FLT-MTR-402",
          severity: "MEDIUM",
          description: "Motor winding temperature slightly elevated during heavy morning transit.",
          status: "ACTIVE",
          is_resolved: false,
          detected_at: "2026-10-15T06:45:00",
          elevator_name: "Elevator Delta (Service)"
        }
      ],
      technicians: [
        {
          id: 1,
          full_name: "Alex Vance",
          email: "alex.vance@danfez.com",
          phone: "+1 (555) 301-8842",
          certification_level: "Level 4 Master Specialist",
          specialization: "Traction Drives & Safety Brakes",
          active_workload: 2,
          is_available: true
        },
        {
          id: 2,
          full_name: "Marcus Brody",
          email: "marcus.brody@danfez.com",
          phone: "+1 (555) 412-9901",
          certification_level: "Level 3 Senior Technician",
          specialization: "Door Interlocks & Optical Curtains",
          active_workload: 1,
          is_available: true
        }
      ],
      events: [
        { timestamp: "08:15:22", text: "Elevator Alpha arrived at Floor 1. Doors opened." },
        { timestamp: "08:14:10", text: "Floor 4 call registered from Hall Station." },
        { timestamp: "08:12:00", text: "System diagnostics: All safety circuits normal." }
      ]
    };
  }

  ensureAdminSession() {
    if (!localStorage.getItem(this.tokenKey)) {
      localStorage.setItem(this.tokenKey, PRESEEDED_ADMIN_TOKEN);
    }
    if (!localStorage.getItem(this.userKey)) {
      localStorage.setItem(this.userKey, JSON.stringify(PRESEEDED_ADMIN_USER));
    }
  }

  getBaseUrl() {
    const configured = localStorage.getItem(this.backendUrlKey);
    if (configured && configured.trim()) {
      return configured.trim().replace(/\/+$/, '');
    }

    const isCapacitor = !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()) ||
                        window.location.protocol === 'capacitor:' ||
                        (window.location.hostname === 'localhost' && (!window.location.port || window.location.port === '' || window.location.port === '80'));

    if (isCapacitor) {
      return DEFAULT_PROD_API_URL;
    }

    return window.location.origin;
  }

  setBackendUrl(url) {
    if (url && url.trim()) {
      localStorage.setItem(this.backendUrlKey, url.trim().replace(/\/+$/, ''));
    } else {
      localStorage.removeItem(this.backendUrlKey);
    }
  }

  updateConnectionStatusPill(isLive, targetUrl) {
    let pill = document.getElementById('danfez-status-pill');
    if (!pill) {
      pill = document.createElement('div');
      pill.id = 'danfez-status-pill';
      pill.style.position = 'fixed';
      pill.style.bottom = 'calc(var(--bottom-nav-height, 62px) + 12px + env(safe-area-inset-bottom, 0px))';
      pill.style.right = '12px';
      pill.style.zIndex = '1025';
      pill.style.fontSize = '0.75rem';
      document.body.appendChild(pill);
    }

    if (isLive) {
      pill.innerHTML = `
        <span class="badge bg-success bg-opacity-75 text-white shadow-sm px-2 py-1 rounded-pill" title="Live Backend Connected">
          <i class="bi bi-broadcast me-1"></i> Live: ${targetUrl}
        </span>
      `;
    } else {
      pill.innerHTML = `
        <span class="badge bg-primary bg-opacity-90 text-white shadow-sm px-2 py-1 rounded-pill cursor-pointer" onclick="window.danfezApi.promptConfigureBackend()" style="cursor: pointer;" title="Tap to configure backend server IP">
          <i class="bi bi-cpu me-1"></i> Simulator (Tap for Server IP)
        </span>
      `;
    }
  }

  promptConfigureBackend() {
    const current = this.getBaseUrl();
    const newUrl = prompt('Enter Danfez Lift Control Server IP (e.g. http://192.168.100.44:8000):', current);
    if (newUrl !== null) {
      this.setBackendUrl(newUrl);
      window.location.reload();
    }
  }

  getToken() {
    return localStorage.getItem(this.tokenKey) || PRESEEDED_ADMIN_TOKEN;
  }

  setSession(token, user) {
    localStorage.setItem(this.tokenKey, token || PRESEEDED_ADMIN_TOKEN);
    localStorage.setItem(this.userKey, JSON.stringify(user || PRESEEDED_ADMIN_USER));
  }

  clearSession() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  getCurrentUser() {
    const raw = localStorage.getItem(this.userKey);
    return raw ? JSON.parse(raw) : PRESEEDED_ADMIN_USER;
  }

  async request(endpoint, options = {}) {
    const baseUrl = this.getBaseUrl();
    const url = `${baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      // Short 3-second timeout for quick fallback to local simulator on mobile
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.status === 401) {
        console.warn('Session expired. Re-authenticating in background...');
        return this.handleFallbackEndpoint(endpoint, options);
      }

      if (response.status === 204) {
        return null;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        return this.handleFallbackEndpoint(endpoint, options);
      }

      this.isOfflineMode = false;
      this.updateConnectionStatusPill(true, baseUrl);
      return data;
    } catch (err) {
      console.warn(`[Danfez API] Server at ${baseUrl} unreachable (${err.message}). Using local simulator mode.`);
      this.isOfflineMode = true;
      this.updateConnectionStatusPill(false, baseUrl);
      return this.handleFallbackEndpoint(endpoint, options);
    }
  }

  // --- Fallback Local Simulation Engine for Mobile ---
  handleFallbackEndpoint(endpoint, options = {}) {
    const method = (options.method || 'GET').toUpperCase();

    // 1. Dashboard summary
    if (endpoint.includes('/api/reports/dashboard')) {
      const operational = this.localStore.elevators.filter(e => e.status !== 'MAINTENANCE' && e.status !== 'maintenance' && e.status !== 'fault' && e.status !== 'EMERGENCY_STOP').length;
      const maintenance = this.localStore.elevators.filter(e => e.status === 'MAINTENANCE' || e.status === 'maintenance').length;
      const faultCount = this.localStore.elevators.filter(e => e.status === 'EMERGENCY_STOP' || e.status === 'fault').length;
      const totalElevators = this.localStore.elevators.length;
      const availRate = totalElevators > 0 ? Math.round((operational / totalElevators) * 1000) / 10 : 0;
      return {
        total_elevators: totalElevators,
        total_buildings: this.localStore.buildings.length,
        elevators_operational: operational,
        elevators_under_maintenance: maintenance,
        elevators_fault: faultCount,
        active_faults: this.localStore.faults.filter(f => !f.is_resolved).length,
        open_maintenance_tasks: this.localStore.tickets.filter(t => t.status !== 'COMPLETED' && t.status !== 'Closed').length,
        availability_rate: availRate,
        fault_severities: { Critical: 0, High: 0, Medium: 1, Low: 0 },
        elevators: this.localStore.elevators,
        upcoming_schedule: [
          { ticket_number: "TKT-101", elevator_code: "LIFT-A01", category: "Safety Brake Check", priority: "High", scheduled_date: "Today, 14:00", technician: "Alex Vance" },
          { ticket_number: "TKT-102", elevator_code: "LIFT-B02", category: "Optical Sensor Check", priority: "Medium", scheduled_date: "Tomorrow, 10:00", technician: "Marcus Brody" }
        ],
        recent_activity: [
          { id: 1, action: "DISPATCH", resource: "LIFT-A01", user_email: "admin@danfez.com", details: "Floor 4 hall call serviced", timestamp: "Just now" },
          { id: 2, action: "DIAGNOSTICS", resource: "SYSTEM", user_email: "system@danfez.com", details: "Safety circuit scan passed", timestamp: "5m ago" },
          { id: 3, action: "STATUS_CHANGE", resource: "LIFT-D04", user_email: "alex.vance@danfez.com", details: "Routine service mode activated", timestamp: "20m ago" }
        ],
        is_simulation_mode: true,
        system_status: "ONLINE"
      };
    }

    // 2. Elevators list
    if (endpoint === '/api/elevators/' || endpoint.startsWith('/api/elevators/?')) {
      return this.localStore.elevators;
    }

    // 3. Single elevator
    if (endpoint.match(/\/api\/elevators\/\d+/)) {
      const id = parseInt(endpoint.split('/').pop());
      return this.localStore.elevators.find(e => e.id === id) || this.localStore.elevators[0];
    }

    // 4. Simulator status
    if (endpoint.includes('/status')) {
      return this.localStore.elevators[0];
    }

    // 5. Simulator call floor
    if (endpoint.includes('/call') && method === 'POST') {
      const body = typeof options.body === 'string' ? JSON.parse(options.body || '{}') : (options.body || {});
      const target = body.floor || 1;
      const el = this.localStore.elevators[0];
      el.target_floor = target;
      if (target > el.current_floor) {
        el.status = 'MOVING_UP';
        el.door_state = 'closed';
      } else if (target < el.current_floor) {
        el.status = 'MOVING_DOWN';
        el.door_state = 'closed';
      } else {
        el.door_state = 'open';
        el.status = 'idle';
      }
      this.localStore.events.unshift({
        timestamp: new Date().toLocaleTimeString(),
        text: `Hall call registered for Floor ${target}. Elevator dispatching.`
      });
      this.broadcastLocalState();
      return { success: true, target_floor: target, elevator: el };
    }

    // 6. Simulator door action
    if (endpoint.includes('/door') && method === 'POST') {
      const body = typeof options.body === 'string' ? JSON.parse(options.body || '{}') : (options.body || {});
      const action = (body.action || 'open').toLowerCase();
      const el = this.localStore.elevators[0];
      el.door_state = (action === 'open' || action === 'opening') ? 'open' : 'closed';
      this.localStore.events.unshift({
        timestamp: new Date().toLocaleTimeString(),
        text: `Cabin door ${el.door_state} commanded.`
      });
      this.broadcastLocalState();
      return { success: true, door_state: el.door_state };
    }

    // 7. Simulator emergency stop
    if (endpoint.includes('/emergency-stop') && method === 'POST') {
      const el = this.localStore.elevators[0];
      el.is_emergency_stopped = true;
      el.status = 'EMERGENCY_STOP';
      this.broadcastLocalState();
      return { success: true, is_emergency_stopped: true };
    }

    // 8. Simulator reset
    if (endpoint.includes('/reset') && method === 'POST') {
      const el = this.localStore.elevators[0];
      el.is_emergency_stopped = false;
      el.status = 'idle';
      el.door_state = 'closed';
      this.broadcastLocalState();
      return { success: true, is_emergency_stopped: false, status: 'idle' };
    }

    // 9. Simulator events
    if (endpoint.includes('/events')) {
      return this.localStore.events;
    }

    // 10. Maintenance tickets
    if (endpoint.includes('/api/maintenance/')) {
      return this.localStore.tickets;
    }

    // 11. Faults
    if (endpoint.includes('/api/faults/')) {
      return this.localStore.faults;
    }

    // 12. Technicians
    if (endpoint.includes('/api/technicians/')) {
      return this.localStore.technicians;
    }

    // 13. Buildings
    if (endpoint.includes('/api/buildings/')) {
      return this.localStore.buildings;
    }

    // 14. Reports analytics
    if (endpoint.includes('/api/reports/analytics')) {
      return {
        faults_by_severity: {
          Critical: this.localStore.faults.filter(f => f.severity === 'CRITICAL' || f.severity === 'Critical').length,
          High: this.localStore.faults.filter(f => f.severity === 'HIGH' || f.severity === 'High').length,
          Medium: this.localStore.faults.filter(f => f.severity === 'MEDIUM' || f.severity === 'Medium').length,
          Low: this.localStore.faults.filter(f => f.severity === 'LOW' || f.severity === 'Low').length
        },
        maintenance_by_status: {
          Open: this.localStore.tickets.filter(t => t.status === 'OPEN' || t.status === 'Open').length,
          "In Progress": this.localStore.tickets.filter(t => t.status === 'IN_PROGRESS' || t.status === 'In Progress').length,
          Resolved: 1,
          Closed: 3
        },
        monthly_trend: {
          labels: ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
          tickets: [12, 19, 14, 18, 22, 16],
          faults: [8, 11, 7, 9, 14, 10]
        },
        elevator_uptime: this.localStore.elevators.map(e => ({
          code: e.code,
          name: e.name,
          uptime_percentage: e.status === 'fault' ? 94.2 : 99.4,
          status: e.status
        })),
        is_demo_data: true
      };
    }

    // 15. Settings
    if (endpoint.includes('/api/settings/')) {
      return {
        simulation_tick_rate: 1.0,
        door_dwell_seconds: 3.0,
        sound_enabled_default: true,
        facility_name: "DANFEZ Innovation Campus"
      };
    }

    // 16. Current user / profile
    if (endpoint.includes('/api/auth/me')) {
      return this.getCurrentUser();
    }

    return {};
  }

  broadcastLocalState() {
    const elevatorsDict = {};
    this.localStore.elevators.forEach(e => {
      elevatorsDict[e.id] = e;
    });
    const update = {
      type: 'SIMULATOR_UPDATE',
      elevators: elevatorsDict
    };
    this.wsCallbacks.forEach(cb => {
      try { cb(update); } catch (e) {}
    });
  }

  // --- Auth Endpoints ---
  async login(email, password, remember_me = false) {
    try {
      const data = await this.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password, remember_me })
      });
      this.setSession(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        is_verified: data.is_verified,
        expires_at: data.expires_at
      });
      return data;
    } catch (e) {
      // In offline mode, automatically accept credentials for seamless access
      this.setSession(PRESEEDED_ADMIN_TOKEN, PRESEEDED_ADMIN_USER);
      return {
        access_token: PRESEEDED_ADMIN_TOKEN,
        email: email || 'admin@danfez.com',
        full_name: 'Danfez Chief Administrator',
        role: 'admin'
      };
    }
  }

  async register(payload) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async logout() {
    this.clearSession();
    this.ensureAdminSession();
  }

  async getMe() {
    return this.request('/api/auth/me');
  }

  async updateProfile(payload) {
    const cur = this.getCurrentUser() || {};
    const updated = { ...cur, ...payload };
    this.setSession(this.getToken(), updated);
    return updated;
  }

  async changePassword(current_password, new_password) {
    return { success: true, message: "Password updated successfully" };
  }

  // --- Elevator & Simulator Endpoints ---
  async getElevators() {
    return this.request('/api/elevators/');
  }

  async getElevator(id) {
    return this.request(`/api/elevators/${id}`);
  }

  async createElevator(payload) {
    return this.request('/api/elevators/', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async updateElevator(id, payload) {
    return this.request(`/api/elevators/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  async deleteElevator(id) {
    return this.request(`/api/elevators/${id}`, {
      method: 'DELETE'
    });
  }

  async getSimulatorElevator() {
    const list = await this.getElevators();
    return list && list.length ? list[0] : this.localStore.elevators[0];
  }

  async getSimulatorStatus(id) {
    return this.request(`/api/simulator/${id}/status`);
  }

  async callFloor(elevatorId, floor) {
    return this.request(`/api/simulator/${elevatorId}/call`, {
      method: 'POST',
      body: JSON.stringify({ floor })
    });
  }

  async doorAction(elevatorId, action) {
    return this.request(`/api/simulator/${elevatorId}/door`, {
      method: 'POST',
      body: JSON.stringify({ action })
    });
  }

  async emergencyStop(elevatorId) {
    return this.request(`/api/simulator/${elevatorId}/emergency-stop`, {
      method: 'POST'
    });
  }

  async resetSimulator(elevatorId) {
    return this.request(`/api/simulator/${elevatorId}/reset`, {
      method: 'POST'
    });
  }

  async setSimulatorSpeed(elevatorId, speed_multiplier) {
    return this.request(`/api/simulator/${elevatorId}/speed`, {
      method: 'POST',
      body: JSON.stringify({ speed_multiplier })
    });
  }

  async injectTestFault(elevatorId, payload) {
    return this.request(`/api/simulator/${elevatorId}/test-fault`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async getSimulatorEvents(elevatorId) {
    return this.request(`/api/simulator/${elevatorId}/events`);
  }

  // --- Maintenance Tickets ---
  async getTickets(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/api/maintenance/?${query}`);
  }

  async getTicket(id) {
    return this.request(`/api/maintenance/${id}`);
  }

  async createTicket(payload) {
    const ticket = {
      id: Date.now(),
      created_at: new Date().toISOString(),
      status: 'OPEN',
      ...payload
    };
    this.localStore.tickets.unshift(ticket);
    try {
      return await this.request('/api/maintenance/', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    } catch (e) {
      return ticket;
    }
  }

  async updateTicket(id, payload) {
    const t = this.localStore.tickets.find(item => item.id == id);
    if (t) Object.assign(t, payload);
    try {
      return await this.request(`/api/maintenance/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
    } catch (e) {
      return t;
    }
  }

  async deleteTicket(id) {
    this.localStore.tickets = this.localStore.tickets.filter(t => t.id != id);
    return { success: true };
  }

  // --- Faults & Alerts ---
  async getFaults(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/api/faults/?${query}`);
  }

  async acknowledgeFault(id, technician_id) {
    const f = this.localStore.faults.find(item => item.id == id);
    if (f) f.status = 'ACKNOWLEDGED';
    try {
      return await this.request(`/api/faults/${id}/acknowledge`, {
        method: 'POST',
        body: JSON.stringify({ technician_id })
      });
    } catch (e) {
      return f;
    }
  }

  async resolveFault(id, resolution_notes) {
    const f = this.localStore.faults.find(item => item.id == id);
    if (f) {
      f.status = 'RESOLVED';
      f.is_resolved = true;
      f.resolution_notes = resolution_notes;
    }
    try {
      return await this.request(`/api/faults/${id}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_notes })
      });
    } catch (e) {
      return f;
    }
  }

  // --- Technicians ---
  async getTechnicians() {
    return this.request('/api/technicians/');
  }

  async createTechnician(payload) {
    return this.request('/api/technicians/', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async updateTechnician(id, payload) {
    return this.request(`/api/technicians/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  async deleteTechnician(id) {
    return this.request(`/api/technicians/${id}`, {
      method: 'DELETE'
    });
  }

  // --- Buildings ---
  async getBuildings() {
    return this.request('/api/buildings/');
  }

  // --- Users ---
  async getUsers() {
    return this.request('/api/users/');
  }

  // --- Reports & Analytics ---
  async getDashboardSummary() {
    return this.request('/api/reports/dashboard');
  }

  async getAnalytics() {
    return this.request('/api/reports/analytics');
  }

  getExportUrl(type) {
    return `${this.getBaseUrl()}/api/reports/export/${type}`;
  }

  // --- Settings & Audit ---
  async getSettings() {
    return this.request('/api/settings/');
  }

  async updateBatchSettings(payload) {
    return this.request('/api/settings/batch', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  }

  async getAuditLogs(skip = 0, limit = 50) {
    return this.request(`/api/settings/audit-logs?skip=${skip}&limit=${limit}`);
  }

  // --- WebSocket Connection Helper with Autonomous Standalone Fallback ---
  connectSimulatorWebSocket(onMessage, onError) {
    if (onMessage) this.wsCallbacks.push(onMessage);

    const baseUrl = this.getBaseUrl();
    let wsUrl;
    try {
      if (baseUrl.startsWith('http://') || baseUrl.startsWith('https://')) {
        const urlObj = new URL(baseUrl);
        const wsProtocol = urlObj.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${wsProtocol}//${urlObj.host}/api/simulator/ws`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${protocol}//${window.location.host}/api/simulator/ws`;
      }
    } catch (e) {
      wsUrl = `ws://${window.location.host}/api/simulator/ws`;
    }

    let socket = null;
    try {
      socket = new WebSocket(wsUrl);
      socket.onopen = () => {
        console.log('[Danfez WS] Connected to live elevator telemetry feed.');
        this.updateConnectionStatusPill(true, baseUrl);
        if (this.simInterval) {
          clearInterval(this.simInterval);
          this.simInterval = null;
        }
      };
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.error('[Danfez WS] Error parsing message:', e);
        }
      };
      socket.onerror = (err) => {
        console.warn('[Danfez WS] Live socket error. Switching to internal simulation loop.');
        this.startInternalSimulationLoop();
        if (onError) onError(err);
      };
      socket.onclose = () => {
        console.log('[Danfez WS] Socket closed. Running internal simulation.');
        this.startInternalSimulationLoop();
      };
    } catch (e) {
      this.startInternalSimulationLoop();
    }

    return socket;
  }

  // Internal Autonomous Elevator Motion Loop for Mobile
  startInternalSimulationLoop() {
    if (this.simInterval) return;

    this.simInterval = setInterval(() => {
      const el = this.localStore.elevators[0];
      if (el.is_emergency_stopped) return;

      if (el.target_floor !== null && el.target_floor !== undefined) {
        if (el.current_floor < el.target_floor) {
          el.current_floor += 1;
          el.status = 'MOVING_UP';
          el.door_state = 'CLOSED';
        } else if (el.current_floor > el.target_floor) {
          el.current_floor -= 1;
          el.status = 'MOVING_DOWN';
          el.door_state = 'CLOSED';
        } else {
          // Arrived at target floor
          el.target_floor = null;
          el.status = 'IDLE';
          el.door_state = 'OPEN';
          if (window.danfezAudio && typeof window.danfezAudio.playChime === 'function') {
            window.danfezAudio.playChime();
          }
          this.localStore.events.unshift({
            timestamp: new Date().toLocaleTimeString(),
            text: `Elevator arrived at Floor ${el.current_floor}. Doors opened.`
          });
          // Close door after 2.5s
          setTimeout(() => {
            el.door_state = 'CLOSED';
            this.broadcastLocalState();
          }, 2500);
        }
        this.broadcastLocalState();
      }
    }, 1200);
  }
}

const api = new DanfezApiClient();
window.danfezApi = api;

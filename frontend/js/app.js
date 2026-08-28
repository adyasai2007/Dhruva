/**
 * DHRUVA - Core Application Script
 * Manages State, Mock Data Loading, Voice Assistant & Global Utilities
 */

const DhruvaApp = (() => {
  const STORAGE_KEY = 'dhruva_app_state_v1';

  // Initial fallback default state
  const defaultState = {
    user: {
      id: 'user-dhruva-01',
      name: 'Dr. Arvind Raghavan',
      age: 52,
      phone: '+91 98450 12345',
      email: 'arvind.raghavan@heritage-travel.in',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80',
      location: 'Bengaluru, India',
      travelPersona: 'Cultural Scholar & Heritage Enthusiast',
      preferredPace: 'Comfortable & Mindful',
      interests: [
        'Heritage',
        'Architecture',
        'Spiritual',
        'Local Culture',
        'History'
      ],
      savedDestinations: ['bhubaneswar', 'puri'],
      savedPlaces: [8, 17],
      activeTrips: []
    },
    settings: {
      largeText: false,
      highContrast: false,
      darkMode: false
    },
    currentPlan: null
  };

  // Load state from localStorage
  const getState = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;
    } catch (e) {
      console.warn('Could not read from localStorage:', e);
      return defaultState;
    }
  };

  // Save state to localStorage
  const saveState = (newState) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newState));
    } catch (e) {
      console.warn('Could not save to localStorage:', e);
    }
  };

  // Fetch mock data with flexible path resolution
  const fetchMockData = async (filename) => {
    // Determine path based on current location
    const basePath = window.location.pathname.includes('/pages/') ? '../mock/' : 'mock/';
    const url = `${basePath}${filename}`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return await res.json();
    } catch (err) {
      // Fallback attempt with direct /mock/ or ../mock/ path if initial fetch failed
      try {
        const fallbackUrl = url.startsWith('../') ? `mock/${filename}` : `../mock/${filename}`;
        const fallbackRes = await fetch(fallbackUrl);
        if (fallbackRes.ok) return await fallbackRes.json();
      } catch (fallbackErr) {
        // Ignore fallback error and log main error below
      }
      console.error(`Error loading mock data from ${url}:`, err);
      return [];
    }
  };

  // Toast Notification System
  const showToast = (message, icon = '✓') => {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  };

  // Bookmark / Save Destination Toggle
  const toggleSaveDestination = (destId, btnElement = null) => {
    const state = getState();
    const saved = state.user.savedDestinations || [];
    const index = saved.indexOf(destId);
    let isSaved = false;

    if (index > -1) {
      saved.splice(index, 1);
      showToast(`Removed from your saved destinations`, 'ℹ');
    } else {
      saved.push(destId);
      isSaved = true;
      showToast(`Added to your saved destinations!`, '★');
    }

    state.user.savedDestinations = saved;
    saveState(state);

    if (btnElement) {
      btnElement.classList.toggle('saved', isSaved);
    }
    return isSaved;
  };

  // Save or Update Active Itinerary Plan
  const saveGeneratedPlan = (planData) => {
    const state = getState();
    state.currentPlan = planData;

    // Add to user activeTrips if not already present
    const existingIndex = state.user.activeTrips.findIndex(t => t.id === planData.id);
    if (existingIndex > -1) {
      state.user.activeTrips[existingIndex] = planData;
    } else {
      state.user.activeTrips.unshift(planData);
    }

    saveState(state);
    showToast(`Journey plan for ${planData.destinationName} saved!`, '✓');
  };

  // Theme Management (Light / Dark Mode)
  const initTheme = () => {
    const state = getState();
    const storedTheme = localStorage.getItem('dhruva_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    const activeTheme = storedTheme || (state.settings?.darkMode ? 'dark' : (prefersDark ? 'dark' : 'light'));

    if (activeTheme === 'dark') {
      document.documentElement.classList.add('dark-theme');
      if (document.body) document.body.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
      if (document.body) document.body.classList.remove('dark-theme');
    }
  };

  const toggleTheme = () => {
    const isDark = document.documentElement.classList.contains('dark-theme') || (document.body && document.body.classList.contains('dark-theme'));
    const newTheme = isDark ? 'light' : 'dark';

    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark-theme');
      if (document.body) document.body.classList.add('dark-theme');
    } else {
      document.documentElement.classList.remove('dark-theme');
      if (document.body) document.body.classList.remove('dark-theme');
    }

    localStorage.setItem('dhruva_theme', newTheme);
    const state = getState();
    if (!state.settings) state.settings = {};
    state.settings.darkMode = (newTheme === 'dark');
    saveState(state);

    showToast(newTheme === 'dark' ? 'Dark Mode (Sacred Night) Enabled' : 'Light Mode (Warm Parchment) Restored', newTheme === 'dark' ? '🌙' : '☀️');
    return newTheme === 'dark';
  };

  // Apply Accessibility Settings
  const applyAccessibilitySettings = () => {
    const state = getState();
    if (!document.body) return;
    if (state.settings && state.settings.largeText) {
      document.body.classList.add('text-scale-large');
    } else {
      document.body.classList.remove('text-scale-large');
    }
    if (state.settings && state.settings.highContrast) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  };

  // Update Header User Profile Display Across Pages
  const updateHeaderUser = () => {
    const state = getState();
    const user = state.user;
    if (!user) return;

    // Update avatar image src and alt
    const avatars = document.querySelectorAll('.nav-avatar');
    avatars.forEach(img => {
      if (user.avatar) img.src = user.avatar;
      img.alt = user.name || 'Traveler';
    });

    // Update user name display if present
    const nameLabels = document.querySelectorAll('[data-user-name], .nav-user-name');
    nameLabels.forEach(el => {
      el.textContent = user.name ? user.name.split(' ')[0] : 'Traveler';
    });
  };

  // Save or Update User Profile & Authentication State
  const saveUser = (userData) => {
    const state = getState();
    state.user = {
      ...state.user,
      ...userData
    };
    saveState(state);
    updateHeaderUser();
    return state.user;
  };

  // Global App Initialization
  // REST API Client helpers for Dhruva Backend
  const apiBase = window.location.origin;

  const apiGet = async (endpoint) => {
    const clean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    try {
      const res = await fetch(`${apiBase}${clean}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn(`apiGet (${clean}) failed:`, e);
      return null;
    }
  };

  const apiPost = async (endpoint, data) => {
    const clean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    try {
      const res = await fetch(`${apiBase}${clean}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      return { ok: res.ok, status: res.status, data: json };
    } catch (e) {
      console.warn(`apiPost (${clean}) failed:`, e);
      return { ok: false, status: 500, error: e.message };
    }
  };

  const apiPatch = async (endpoint, data) => {
    const clean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    try {
      const res = await fetch(`${apiBase}${clean}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const json = await res.json();
      return { ok: res.ok, status: res.status, data: json };
    } catch (e) {
      console.warn(`apiPatch (${clean}) failed:`, e);
      return { ok: false, status: 500, error: e.message };
    }
  };

  const apiDelete = async (endpoint) => {
    const clean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    try {
      const res = await fetch(`${apiBase}${clean}`, { method: 'DELETE' });
      const json = await res.json();
      return { ok: res.ok, status: res.status, data: json };
    } catch (e) {
      console.warn(`apiDelete (${clean}) failed:`, e);
      return { ok: false, status: 500, error: e.message };
    }
  };

  const init = () => {
    initTheme();
    applyAccessibilitySettings();
    updateHeaderUser();
  };

  return {
    init,
    initTheme,
    toggleTheme,
    getState,
    saveState,
    saveUser,
    updateHeaderUser,
    fetchMockData,
    apiGet,
    apiPost,
    apiPatch,
    apiDelete,
    showToast,
    toggleSaveDestination,
    saveGeneratedPlan,
    applyAccessibilitySettings
  };
})();

// Immediate theme execution to prevent FOUC
DhruvaApp.initTheme();
document.addEventListener('DOMContentLoaded', DhruvaApp.init);

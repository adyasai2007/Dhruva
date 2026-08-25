/**
 * DHRUVA - Core Application Script
 * Manages State, Mock Data Loading, Voice Assistant & Global Utilities
 */

const DhruvaApp = (() => {
  const STORAGE_KEY = 'dhruva_app_state_v1';

  // Initial fallback default state
  const defaultState = {
    user: {
      name: 'Dr. Arvind Raghavan',
      savedDestinations: ['varanasi', 'hampi'],
      savedPlaces: ['dashashwamedh-ghat', 'vittala-temple-hampi'],
      activeTrips: []
    },
    settings: {
      largeText: false,
      highContrast: false
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
    const basePath = window.location.pathname.includes('/pages/') ? '../data/mock/' : 'data/mock/';
    const url = `${basePath}${filename}`;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return await res.json();
    } catch (err) {
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

  // Global App Initialization
  const init = () => {
    initTheme();
    applyAccessibilitySettings();
  };

  return {
    init,
    initTheme,
    toggleTheme,
    getState,
    saveState,
    fetchMockData,
    showToast,
    toggleSaveDestination,
    saveGeneratedPlan,
    applyAccessibilitySettings
  };
})();

// Immediate theme execution to prevent FOUC
DhruvaApp.initTheme();
document.addEventListener('DOMContentLoaded', DhruvaApp.init);

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

  // Apply saved accessibility preferences
  const applyAccessibilitySettings = () => {
    const state = getState();
    if (state.settings?.largeText) {
      document.body.classList.add('text-scale-large');
    } else {
      document.body.classList.remove('text-scale-large');
    }
    if (state.settings?.highContrast) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  };

  // Voice Assistant Modal Logic
  const initVoiceModal = () => {
    const voiceBtns = document.querySelectorAll('[data-action="open-voice"]');
    const modal = document.getElementById('voice-assistant-modal');
    if (!modal) return;

    const closeBtn = modal.querySelector('.modal-close-btn');
    const promptChips = modal.querySelectorAll('.voice-prompt-chip');
    const statusText = modal.querySelector('.voice-status-text');

    voiceBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.add('active');
      });
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    }

    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('active');
    });

    promptChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.dataset.promptText || chip.textContent.trim();
        if (statusText) {
          statusText.textContent = `Understanding: "${text}"...`;
          setTimeout(() => {
            modal.classList.remove('active');
            if (text.toLowerCase().includes('varanasi')) {
              window.location.href = window.location.pathname.includes('/pages/') 
                ? 'trip.html?dest=varanasi' 
                : 'pages/trip.html?dest=varanasi';
            } else if (text.toLowerCase().includes('hampi')) {
              window.location.href = window.location.pathname.includes('/pages/') 
                ? 'trip.html?dest=hampi' 
                : 'pages/trip.html?dest=hampi';
            } else {
              window.location.href = window.location.pathname.includes('/pages/') 
                ? 'explore.html' 
                : 'pages/explore.html';
            }
          }, 1200);
        }
      });
    });
  };

  // Global App Initialization
  const init = () => {
    applyAccessibilitySettings();
    initVoiceModal();
  };

  return {
    init,
    getState,
    saveState,
    fetchMockData,
    showToast,
    toggleSaveDestination,
    saveGeneratedPlan,
    applyAccessibilitySettings
  };
})();

document.addEventListener('DOMContentLoaded', DhruvaApp.init);

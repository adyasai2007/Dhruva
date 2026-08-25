/**
 * DHRUVA - Navigation & Responsive Shell Controller
 */

const DhruvaNavigation = (() => {
  const init = () => {
    highlightActivePage();
    setupHeaderScroll();
    setupMobileMenu();
    setupKeyboardListeners();
    setupAccessibilityToggles();
  };

  // Mark current nav link as active
  const highlightActivePage = () => {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (!href) return;

      // Match home page
      if ((currentPath.endsWith('index.html') || currentPath.endsWith('/') || currentPath.endsWith('Dhruva/')) && (href === 'index.html' || href === '../index.html')) {
        link.classList.add('active');
      } 
      // Match other pages
      else if (href.includes('/') && currentPath.endsWith(href.split('/').pop())) {
        link.classList.add('active');
      } else if (currentPath.endsWith(href)) {
        link.classList.add('active');
      }
    });
  };

  // Add shadow and solid surface to header when scrolled
  const setupHeaderScroll = () => {
    const header = document.querySelector('.site-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }, { passive: true });
  };

  // Toggle mobile navigation drawer
  const setupMobileMenu = () => {
    const menuBtn = document.querySelector('.menu-toggle-btn');
    const navLinks = document.querySelector('.nav-links');

    if (!menuBtn || !navLinks) return;

    menuBtn.addEventListener('click', () => {
      const isExpanded = menuBtn.getAttribute('aria-expanded') === 'true';
      menuBtn.setAttribute('aria-expanded', !isExpanded);
      navLinks.classList.toggle('open');
      
      // Toggle hamburger to close icon
      menuBtn.innerHTML = navLinks.classList.contains('open')
        ? `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`
        : `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
      if (navLinks.classList.contains('open') && !navLinks.contains(e.target) && !menuBtn.contains(e.target)) {
        navLinks.classList.remove('open');
        menuBtn.setAttribute('aria-expanded', 'false');
      }
    });
  };

  // Close open modals when Escape key is pressed
  const setupKeyboardListeners = () => {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const activeModals = document.querySelectorAll('.modal-overlay.active');
        activeModals.forEach(m => m.classList.remove('active'));
      }
    });
  };

  // Setup Accessibility Toggles if present
  const setupAccessibilityToggles = () => {
    const fontToggle = document.querySelector('[data-action="toggle-font-scale"]');
    if (fontToggle) {
      fontToggle.addEventListener('click', () => {
        const state = DhruvaApp.getState();
        state.settings.largeText = !state.settings.largeText;
        DhruvaApp.saveState(state);
        DhruvaApp.applyAccessibilitySettings();
        DhruvaApp.showToast(state.settings.largeText ? 'Large Text Mode Enabled' : 'Standard Text Mode Enabled');
      });
    }
  };

  return { init };
})();

document.addEventListener('DOMContentLoaded', DhruvaNavigation.init);

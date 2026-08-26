/**
 * DHRUVA - Reusable UI Component Renderers
 */

const DhruvaComponents = (() => {
  // Render Destination Card
  const renderDestinationCard = (dest, isSaved = false, isRootPath = false) => {
    const tripPageUrl = isRootPath ? `pages/trip.html?dest=${dest.id}` : `trip.html?dest=${dest.id}`;
    const explorePageUrl = isRootPath ? `pages/explore.html?dest=${dest.id}` : `explore.html?dest=${dest.id}`;

    return `
      <article class="card-destination" data-destination-id="${dest.id}" data-region="${dest.region}">
        <div class="card-destination-image-box">
          <img class="card-destination-image" src="${dest.thumbnailImage || dest.heroImage}" alt="${dest.name}" loading="lazy">
          <span class="badge card-destination-region">${dest.region}</span>
          <button class="card-destination-save-btn ${isSaved ? 'saved' : ''}" 
                  aria-label="Save ${dest.name} to my wishlist" 
                  onclick="DhruvaApp.toggleSaveDestination('${dest.id}', this)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
            </svg>
          </button>
        </div>
        <div class="card-destination-body">
          <div class="card-destination-title-row">
            <h3 class="card-destination-title font-serif">${dest.name}</h3>
            <span class="card-destination-places-count">${dest.placeCount} places</span>
          </div>
          <p class="card-destination-tagline">${dest.tagline}</p>
          <p class="card-destination-desc">${dest.description}</p>
          
          <div class="card-destination-meta">
            <div class="card-destination-best-time">
              <span class="card-destination-meta-label">Best Season</span>
              <span class="card-destination-meta-val">${dest.bestTime?.idealMonths || 'Oct - Mar'}</span>
            </div>
            <div style="display: flex; gap: var(--space-2);">
              <a href="${explorePageUrl}" class="btn btn-secondary btn-sm">Explore</a>
              <a href="${tripPageUrl}" class="btn btn-primary btn-sm">Plan Trip</a>
            </div>
          </div>
        </div>
      </article>
    `;
  };

  // Render Place Card
  const renderPlaceCard = (place) => {
    return `
      <article class="card-place" data-place-id="${place.id}" data-category="${place.category}">
        <div class="card-place-image-wrap">
          <img class="card-place-image" src="${place.image}" alt="${place.name}" loading="lazy">
          <span class="badge card-place-category">${place.category}</span>
        </div>
        <div class="card-place-body">
          <h3 class="card-place-title font-serif">${place.name}</h3>
          <p class="card-place-desc">${place.shortDescription}</p>
          
          <div class="card-place-info-chips">
            <span class="info-chip">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              ${place.recommendedDuration}
            </span>
            <span class="info-chip">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path></svg>
              ${place.bestTimeOfDay}
            </span>
          </div>

          <div class="card-place-footer">
            <span style="font-size: var(--font-size-xs); color: var(--color-text-muted);">${place.openingHours}</span>
            <button class="btn btn-outline btn-sm" onclick="DhruvaComponents.openPlaceDetailsModal('${place.id}')">
              Cultural Details
            </button>
          </div>
        </div>
      </article>
    `;
  };

  // Render Cultural Event Card
  const renderEventCard = (event) => {
    return `
      <article class="card-place" data-event-id="${event.id}">
        <div class="card-place-image-wrap">
          <img class="card-place-image" src="${event.image}" alt="${event.name}" loading="lazy">
          <span class="badge badge-accent card-place-category">${event.period}</span>
        </div>
        <div class="card-place-body">
          <span class="eyebrow">${event.category}</span>
          <h3 class="card-place-title font-serif">${event.name}</h3>
          <p class="card-place-desc">${event.description}</p>
          <div class="cultural-note-box">
            <strong>Travel Wisdom:</strong> ${event.travelTips}
          </div>
        </div>
      </article>
    `;
  };

  // Open Place Details Modal with Cultural Context
  const openPlaceDetailsModal = async (placeId) => {
    let places = window._cachedPlaces;
    if (!places) {
      places = await DhruvaApp.fetchMockData('places.json');
      window._cachedPlaces = places;
    }
    const place = places.find(p => p.id === placeId);
    if (!place) return;

    let modal = document.getElementById('place-detail-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'place-detail-modal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <div>
            <span class="badge badge-primary">${place.category}</span>
            <h3 class="modal-title font-serif" style="margin-top: 4px; font-size: 1.5rem;">${place.name}</h3>
          </div>
          <button class="modal-close-btn" onclick="document.getElementById('place-detail-modal').classList.remove('active')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="modal-body">
          <img src="${place.image}" alt="${place.name}" style="width: 100%; border-radius: var(--radius-md); margin-bottom: var(--space-4); max-height: 280px; object-fit: cover;">
          <p class="lead-text" style="font-size: var(--font-size-base); margin-bottom: var(--space-4);">${place.fullDescription || place.shortDescription}</p>
          
          <div class="cultural-note-box" style="margin-bottom: var(--space-5);">
            <strong>Cultural & Historical Significance:</strong><br>
            ${place.culturalSignificance}
          </div>

          <div class="grid-2" style="gap: var(--space-3); margin-bottom: var(--space-4);">
            <div style="background: var(--color-surface-soft); padding: var(--space-3); border-radius: var(--radius-sm);">
              <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-muted);">Recommended Time</span>
              <p style="font-weight: 600; font-size: 0.875rem;">${place.bestTimeOfDay}</p>
            </div>
            <div style="background: var(--color-surface-soft); padding: var(--space-3); border-radius: var(--radius-sm);">
              <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-muted);">Entry & Access</span>
              <p style="font-weight: 600; font-size: 0.875rem;">${place.entryFee || 'Free'}</p>
            </div>
          </div>

          ${place.tips ? `
            <p style="font-size: var(--font-size-xs); color: var(--color-text-secondary); line-height: 1.5;">
              <strong>Visitor Tip:</strong> ${place.tips}
            </p>
          ` : ''}
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('place-detail-modal').classList.remove('active')">Close</button>
          <button class="btn btn-primary btn-sm" onclick="DhruvaApp.showToast('Place added to your custom journey!'); document.getElementById('place-detail-modal').classList.remove('active');">
            Add to Itinerary
          </button>
        </div>
      </div>
    `;

    modal.classList.add('active');
    modal.onclick = (e) => {
      if (e.target === modal) modal.classList.remove('active');
    };
  };

  return {
    renderDestinationCard,
    renderPlaceCard,
    renderEventCard,
    openPlaceDetailsModal
  };
})();

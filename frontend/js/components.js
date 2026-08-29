/**
 * DHRUVA - Reusable UI Component Renderers
 */

const DhruvaComponents = (() => {
  const fallbackImages = {
    bhubaneswar: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg',
    puri: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Konarka_Temple.jpg/960px-Konarka_Temple.jpg',
    cuttack: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Entrance_of_Barabati_fort.jpg/960px-Entrance_of_Barabati_fort.jpg',
    default: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg'
  };

  // Render Destination Card
  const renderDestinationCard = (dest, isSaved = false, isRootPath = false) => {
    const tripPageUrl = isRootPath ? `pages/trip.html?dest=${dest.id}` : `trip.html?dest=${dest.id}`;
    const explorePageUrl = isRootPath ? `pages/explore.html?dest=${dest.id}` : `explore.html?dest=${dest.id}`;
    const imgSrc = dest.thumbnailImage || dest.heroImage || fallbackImages[dest.id] || fallbackImages.default;

    return `
      <article class="card-destination" data-destination-id="${dest.id}" data-region="${dest.region}">
        <div class="card-destination-image-box">
          <img class="card-destination-image" src="${imgSrc}" alt="${dest.name}" loading="lazy" onerror="this.onerror=null; this.src='${fallbackImages[dest.id] || fallbackImages.default}';">
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
    const matchPct = place.match_percentage || (place.match_score ? Math.round(place.match_score * 100) : (place.popularity ? Math.round(place.popularity * 20) : null));
    const durationText = place.duration_label || place.recommendedDuration || (place.duration ? `${place.duration} hrs` : '2 hrs');
    const feeText = place.entry_fee || place.entryFee || 'Free entry';
    const subCat = place.sub_category ? `<span class="eyebrow" style="font-size: 0.75rem; color: var(--color-primary); margin-bottom: 2px;">${place.sub_category}</span>` : '';
    const imgUrl = place.image_url || place.image || fallbackImages.default;

    return `
      <article class="card-place" data-place-id="${place.id}" data-category="${place.category}">
        <div class="card-place-image-wrap">
          <img class="card-place-image" src="${imgUrl}" alt="${place.name}" loading="lazy" onerror="this.onerror=null; this.src='${fallbackImages.default}';">
          <span class="badge card-place-category">${place.category}</span>
          ${matchPct ? `<span class="badge badge-accent" style="position: absolute; bottom: 10px; right: 10px; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">✨ ${matchPct}% Match</span>` : ''}
        </div>
        <div class="card-place-body">
          ${subCat}
          <h3 class="card-place-title font-serif">${place.name}</h3>
          <p class="card-place-desc">${place.shortDescription || place.description || ''}</p>
          
          <div class="card-place-info-chips">
            <span class="info-chip" title="Recommended Visit Duration">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
              ${durationText}
            </span>
            <span class="info-chip" title="Entry Fee / Ticket Status">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 12V8H6a2 2 0 0 1-2-2V4h16v4"></path><path d="M4 6v14a2 2 0 0 0 2 2h14v-4"></path><circle cx="12" cy="14" r="2"></circle></svg>
              ${feeText.length > 24 ? feeText.substring(0, 22) + '...' : feeText}
            </span>
          </div>

          <div class="card-place-footer">
            <span style="font-size: var(--font-size-xs); color: var(--color-text-muted);">
              ${place.source ? `Source: ${place.source}` : 'Cultural Sanctum'}
            </span>
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
    if (!places || places.length === 0) {
      const apiPlaces = await DhruvaApp.apiGet('/api/places');
      if (apiPlaces && Array.isArray(apiPlaces) && apiPlaces.length > 0) {
        places = apiPlaces;
      } else {
        places = await DhruvaApp.fetchMockData('places.json');
      }
      window._cachedPlaces = places;
    }

    let place = (places || []).find(p => String(p.id) === String(placeId));
    if (!place) {
      const res = await DhruvaApp.apiGet(`/api/places/${placeId}`);
      if (res && res.data) place = res.data;
    }
    if (!place) return;

    let modal = document.getElementById('place-detail-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'place-detail-modal';
      modal.className = 'modal-overlay';
      document.body.appendChild(modal);
    }

    const imgUrl = place.image_url || place.image || 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Lingaraj_Temple_%2C_Bhubaneswar.jpg/960px-Lingaraj_Temple_%2C_Bhubaneswar.jpg';
    const descText = place.fullDescription || place.description || place.shortDescription || '';
    const feeText = place.entry_fee || place.entryFee || 'Free entry';
    const durText = place.duration_label || place.recommendedDuration || (place.duration ? `${place.duration} hrs` : '2 hrs');
    const cultSignificance = place.culturalSignificance || `${place.name} is a renowned cultural and spiritual monument in Odisha, showcasing distinctive architecture and heritage.`;

    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-header">
          <div>
            <span class="badge badge-primary">${place.category || 'Cultural Landmark'}</span>
            <h3 class="modal-title font-serif" style="margin-top: 4px; font-size: 1.5rem;">${place.name}</h3>
          </div>
          <button class="modal-close-btn" onclick="document.getElementById('place-detail-modal').classList.remove('active')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div class="modal-body">
          <img src="${imgUrl}" alt="${place.name}" style="width: 100%; border-radius: var(--radius-md); margin-bottom: var(--space-4); max-height: 280px; object-fit: cover;">
          <p class="lead-text" style="font-size: var(--font-size-base); margin-bottom: var(--space-4);">${descText}</p>
          
          <div class="cultural-note-box" style="margin-bottom: var(--space-4);">
            <strong>Cultural & Historical Significance:</strong><br>
            ${cultSignificance}
          </div>

          <div class="grid-2" style="gap: var(--space-3); margin-bottom: var(--space-4);">
            <div style="background: var(--color-surface-soft); padding: var(--space-3); border-radius: var(--radius-sm);">
              <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-muted);">Recommended Time</span>
              <p style="font-weight: 600; font-size: 0.875rem;">${durText}</p>
            </div>
            <div style="background: var(--color-surface-soft); padding: var(--space-3); border-radius: var(--radius-sm);">
              <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-muted);">Entry & Access</span>
              <p style="font-weight: 600; font-size: 0.875rem;">${feeText}</p>
            </div>
          </div>

          ${place.interests ? `
            <div style="margin-bottom: var(--space-4); background: var(--color-surface-soft); padding: var(--space-3); border-radius: var(--radius-sm);">
              <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-muted); display: block; margin-bottom: 6px; font-weight: 600;">Cultural Interest Dimensions (MIN_INTEREST)</span>
              <div style="display: flex; flex-wrap: wrap; gap: 6px; font-size: 0.75rem;">
                <span class="badge badge-outline" style="border-color: var(--color-border);">🏛️ Arch: ${place.interests.architecture || 0}/5</span>
                <span class="badge badge-outline" style="border-color: var(--color-border);">📜 Hist: ${place.interests.history || 0}/5</span>
                <span class="badge badge-outline" style="border-color: var(--color-border);">🕉️ Spirit: ${place.interests.spiritual || 0}/5</span>
                <span class="badge badge-outline" style="border-color: var(--color-border);">🌿 Nature: ${place.interests.nature || 0}/5</span>
                <span class="badge badge-outline" style="border-color: var(--color-border);">🎭 Cult: ${place.interests.culture || 0}/5</span>
              </div>
            </div>
          ` : ''}

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

/**
 * DHRUVA - Guided Trip Planner Logic
 * Multi-Step Conversational Planner & Dynamic Itinerary Synthesizer
 * Integrated with DHRUVA Backend Routing & Utility Optimization Engine
 */

const DhruvaPlanner = (() => {
  let currentStep = 1;
  const totalSteps = 4;

  const planState = {
    destinationId: 'bhubaneswar',
    destinationName: 'Bhubaneswar',
    cityId: 1,
    mode: 'full_trip', // 'full_trip' or 'quick_visit'
    startDate: '',
    durationDays: 3,
    availableMinutes: 240,
    pace: 'Comfortable & Mindful',
    dailyStartTime: '08:30 AM',
    dailyEndTime: '07:30 PM',
    interests: ['Heritage', 'Spiritual', 'Local Culture'],
    travelGroup: 'Solo / Senior Friendly',
    mandatoryPlaceIds: []
  };

  let destinationsData = [];
  let placesData = [];
  let currentCityPlaces = [];

  const cityIdMap = {
    'bhubaneswar': 1,
    'puri': 2,
    'cuttack': 3
  };

  const init = async () => {
    // 1. Try loading cities dynamically from backend API; fallback to destinations.json
    const apiCities = await DhruvaApp.apiGet('/api/cities');
    const mockDestinations = await DhruvaApp.fetchMockData('destinations.json');

    if (apiCities && Array.isArray(apiCities) && apiCities.length > 0) {
      destinationsData = apiCities.map(c => {
        const mockMatch = (mockDestinations || []).find(m => m.name.toLowerCase() === c.name.toLowerCase() || m.cityId === c.id);
        return {
          id: c.name.toLowerCase(),
          name: c.name,
          cityId: c.id,
          state: c.state || 'Odisha',
          region: 'East India',
          lat: c.lat,
          long: c.long,
          tagline: mockMatch ? mockMatch.tagline : `${c.name}, Odisha`,
          description: mockMatch ? mockMatch.description : `Historic cultural capital in Odisha`,
          heroImage: mockMatch ? mockMatch.heroImage : 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173',
          thumbnailImage: mockMatch ? mockMatch.thumbnailImage : 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173',
          bestTime: mockMatch ? mockMatch.bestTime : { idealMonths: 'October to March' },
          placeCount: c.place_count || 8
        };
      });
    } else {
      destinationsData = mockDestinations || [];
    }

    // Load places dataset
    placesData = await DhruvaApp.fetchMockData('places.json');

    // Parse URL params for pre-selection (e.g., ?dest=puri)
    const urlParams = new URLSearchParams(window.location.search);
    const destParam = urlParams.get('dest');
    if (destParam && destinationsData.some(d => d.id === destParam.toLowerCase())) {
      planState.destinationId = destParam.toLowerCase();
      const found = destinationsData.find(d => d.id === planState.destinationId);
      planState.destinationName = found.name;
      planState.cityId = found.cityId || cityIdMap[planState.destinationId] || 1;
    } else {
      planState.destinationId = 'bhubaneswar';
      planState.destinationName = 'Bhubaneswar';
      planState.cityId = 1;
    }

    renderDestinationSelector();
    setupEventListeners();
    loadCityPlaces(planState.destinationName);
    updateStepUI();
    updateLiveSummary();
  };

  // Populate Destination Cards / Radio Options
  const renderDestinationSelector = () => {
    const container = document.getElementById('planner-destinations-grid');
    if (!container) return;

    container.innerHTML = destinationsData.map(dest => {
      const isSelected = dest.id === planState.destinationId;
      return `
        <div class="planner-dest-option ${isSelected ? 'selected' : ''}" data-dest-id="${dest.id}" onclick="DhruvaPlanner.selectDestination('${dest.id}')">
          <img src="${dest.thumbnailImage}" alt="${dest.name}" class="planner-dest-thumb">
          <div class="planner-dest-info">
            <h4 class="font-serif">${dest.name}</h4>
            <span class="planner-dest-region">${dest.region || 'East India'} • ${dest.state}</span>
            <span class="badge badge-primary" style="margin-top: 4px;">Best: ${dest.bestTime ? dest.bestTime.idealMonths : 'Oct - Mar'}</span>
          </div>
          <div class="planner-dest-check">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </div>
        </div>
      `;
    }).join('');
  };

  // Select Destination handler
  const selectDestination = (destId) => {
    planState.destinationId = destId;
    const dest = destinationsData.find(d => d.id === destId);
    if (dest) {
      planState.destinationName = dest.name;
      planState.cityId = dest.cityId || cityIdMap[destId] || 1;
    }
    
    document.querySelectorAll('.planner-dest-option').forEach(el => {
      el.classList.toggle('selected', el.dataset.destId === destId);
    });

    planState.mandatoryPlaceIds = [];
    loadCityPlaces(planState.destinationName);
    updateLiveSummary();
  };

  // Load places for the chosen city to allow mandatory place selection
  const loadCityPlaces = async (cityName) => {
    const listContainer = document.getElementById('planner-mandatory-places-list');
    if (!listContainer) return;

    listContainer.innerHTML = '<span class="text-muted" style="font-size: var(--font-size-xs);">Loading places for ' + cityName + '...</span>';

    // Try backend API first
    const apiPlaces = await DhruvaApp.apiGet(`/api/places?city_name=${encodeURIComponent(cityName)}&limit=25`);
    if (apiPlaces && Array.isArray(apiPlaces) && apiPlaces.length > 0) {
      currentCityPlaces = apiPlaces;
    } else {
      // Fallback to local placesData filtered by destination
      currentCityPlaces = (placesData || []).filter(p => 
        (p.destinationId && p.destinationId.toLowerCase() === cityName.toLowerCase()) ||
        p.cityId === planState.cityId
      );
    }

    if (currentCityPlaces.length === 0) {
      listContainer.innerHTML = '<span class="text-muted" style="font-size: var(--font-size-xs);">No places available.</span>';
      return;
    }

    listContainer.innerHTML = currentCityPlaces.map(p => {
      const isChecked = planState.mandatoryPlaceIds.includes(p.id);
      return `
        <label style="display: flex; align-items: flex-start; gap: 8px; font-size: var(--font-size-xs); cursor: pointer; padding: 6px; border-radius: var(--radius-sm); background: var(--color-surface); border: 1px solid var(--color-border);">
          <input type="checkbox" value="${p.id}" ${isChecked ? 'checked' : ''} onchange="DhruvaPlanner.toggleMandatoryPlace(${p.id}, this.checked)" style="margin-top: 2px;">
          <div>
            <strong style="color: var(--color-text); display: block;">${p.name}</strong>
            <span class="text-muted">${p.category || 'Heritage'} • ${p.duration_label || (p.duration ? p.duration + 'h' : '2h')}</span>
          </div>
        </label>
      `;
    }).join('');
  };

  const toggleMandatoryPlace = (placeId, isChecked) => {
    if (isChecked) {
      if (!planState.mandatoryPlaceIds.includes(placeId)) {
        planState.mandatoryPlaceIds.push(placeId);
      }
    } else {
      planState.mandatoryPlaceIds = planState.mandatoryPlaceIds.filter(id => id !== placeId);
    }
  };

  const setTripMode = (mode) => {
    planState.mode = mode;
    const btnFull = document.getElementById('btn-mode-full');
    const btnQuick = document.getElementById('btn-mode-quick');
    const fullGroup = document.getElementById('full-trip-duration-group');
    const quickGroup = document.getElementById('quick-visit-duration-group');

    if (mode === 'quick_visit') {
      if (btnFull) { btnFull.classList.remove('btn-primary'); btnFull.classList.add('btn-secondary'); }
      if (btnQuick) { btnQuick.classList.remove('btn-secondary'); btnQuick.classList.add('btn-primary'); }
      if (fullGroup) fullGroup.style.display = 'none';
      if (quickGroup) quickGroup.style.display = 'block';
    } else {
      if (btnFull) { btnFull.classList.remove('btn-secondary'); btnFull.classList.add('btn-primary'); }
      if (btnQuick) { btnQuick.classList.remove('btn-primary'); btnQuick.classList.add('btn-secondary'); }
      if (fullGroup) fullGroup.style.display = 'block';
      if (quickGroup) quickGroup.style.display = 'none';
    }
    updateLiveSummary();
  };

  const setCustomDays = (val) => {
    let days = parseInt(val, 10);
    if (isNaN(days) || days < 1) days = 1;
    if (days > 30) days = 30;
    planState.durationDays = days;

    const input = document.getElementById('planner-custom-days-input');
    if (input && parseInt(input.value, 10) !== days) {
      input.value = days;
    }

    document.querySelectorAll('[data-duration-days]').forEach(b => {
      b.classList.toggle('active', parseInt(b.dataset.durationDays, 10) === days);
    });

    updateLiveSummary();
  };

  const adjustDays = (delta) => {
    const current = planState.durationDays || 3;
    const nextDays = Math.max(1, Math.min(30, current + delta));
    setCustomDays(nextDays);
  };

  const setQuickMinutes = (mins) => {
    planState.availableMinutes = mins;
    const hrs = mins / 60;
    const input = document.getElementById('planner-custom-hours-input');
    if (input) input.value = hrs;

    document.querySelectorAll('[data-quick-minutes]').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.quickMinutes, 10) === mins);
    });
    updateLiveSummary();
  };

  const setCustomHours = (val) => {
    let hrs = parseFloat(val);
    if (isNaN(hrs) || hrs < 0.5) hrs = 0.5;
    if (hrs > 14) hrs = 14;
    planState.availableMinutes = Math.round(hrs * 60);

    const input = document.getElementById('planner-custom-hours-input');
    if (input && parseFloat(input.value) !== hrs) {
      input.value = hrs;
    }

    document.querySelectorAll('[data-quick-minutes]').forEach(btn => {
      btn.classList.toggle('active', parseInt(btn.dataset.quickMinutes, 10) === planState.availableMinutes);
    });
    updateLiveSummary();
  };

  const adjustHours = (delta) => {
    const currentHrs = (planState.availableMinutes || 240) / 60;
    const nextHrs = Math.max(1, Math.min(14, currentHrs + delta));
    setCustomHours(nextHrs);
  };

  const setTimeWindow = (type, timeVal) => {
    if (!timeVal) return;
    const parts = timeVal.split(':');
    let h = parseInt(parts[0], 10);
    const m = parts[1] || '00';
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    const formatted = `${String(h12).padStart(2, '0')}:${m} ${ampm}`;

    if (type === 'start') {
      planState.dailyStartTime = formatted;
    } else {
      planState.dailyEndTime = formatted;
    }
    updateLiveSummary();
  };

  // Setup Event Listeners for Step Controls
  const setupEventListeners = () => {
    // Next Step Button
    const nextBtn = document.getElementById('planner-btn-next');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (currentStep < totalSteps) {
          currentStep++;
          updateStepUI();
        } else {
          generateItinerary();
        }
      });
    }

    // Prev Step Button
    const prevBtn = document.getElementById('planner-btn-prev');
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
          currentStep--;
          updateStepUI();
        }
      });
    }

    // Duration Day Buttons
    document.querySelectorAll('[data-duration-days]').forEach(btn => {
      btn.addEventListener('click', () => {
        setCustomDays(parseInt(btn.dataset.durationDays, 10));
      });
    });

    // Pacing Buttons
    document.querySelectorAll('[data-pace-option]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-pace-option]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        planState.pace = btn.dataset.paceOption;
        updateLiveSummary();
      });
    });

    // Interest Chips
    document.querySelectorAll('[data-interest-name]').forEach(chip => {
      chip.addEventListener('click', () => {
        const interest = chip.dataset.interestName;
        chip.classList.toggle('active');
        
        if (chip.classList.contains('active')) {
          if (!planState.interests.includes(interest)) planState.interests.push(interest);
        } else {
          planState.interests = planState.interests.filter(i => i !== interest);
        }
        updateLiveSummary();
      });
    });

    // Date Input Listener
    const dateInput = document.getElementById('planner-start-date');
    if (dateInput) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      dateInput.valueAsDate = tomorrow;
      planState.startDate = dateInput.value;

      dateInput.addEventListener('change', (e) => {
        planState.startDate = e.target.value;
        updateLiveSummary();
      });
    }

    // Daily Start and End Time Listeners
    const startTimeInput = document.getElementById('planner-start-time');
    if (startTimeInput) {
      const updateStart = (e) => setTimeWindow('start', e.target.value);
      startTimeInput.addEventListener('change', updateStart);
      startTimeInput.addEventListener('input', updateStart);
      if (startTimeInput.value) setTimeWindow('start', startTimeInput.value);
    }
    const endTimeInput = document.getElementById('planner-end-time');
    if (endTimeInput) {
      const updateEnd = (e) => setTimeWindow('end', e.target.value);
      endTimeInput.addEventListener('change', updateEnd);
      endTimeInput.addEventListener('input', updateEnd);
      if (endTimeInput.value) setTimeWindow('end', endTimeInput.value);
    }
  };

  // Update wizard UI display per step
  const updateStepUI = () => {
    for (let i = 1; i <= totalSteps; i++) {
      const stepSection = document.getElementById(`planner-step-${i}`);
      const stepIndicator = document.getElementById(`step-indicator-${i}`);
      
      if (stepSection) {
        stepSection.style.display = i === currentStep ? 'block' : 'none';
      }
      if (stepIndicator) {
        stepIndicator.classList.toggle('active', i === currentStep);
        stepIndicator.classList.toggle('completed', i < currentStep);
      }
    }

    const prevBtn = document.getElementById('planner-btn-prev');
    const nextBtn = document.getElementById('planner-btn-next');

    if (prevBtn) {
      prevBtn.style.visibility = currentStep === 1 ? 'hidden' : 'visible';
    }

    if (nextBtn) {
      nextBtn.textContent = currentStep === totalSteps ? 'Generate My Cultural Plan' : 'Continue';
      if (currentStep === totalSteps) {
        nextBtn.classList.add('btn-primary');
      }
    }

    window.scrollTo({ top: 120, behavior: 'smooth' });
  };

  // Update live preview sidebar
  const updateLiveSummary = () => {
    const summaryDest = document.getElementById('summary-destination');
    const summaryDays = document.getElementById('summary-duration');
    const summaryWindow = document.getElementById('summary-window');
    const summaryPace = document.getElementById('summary-pace');
    const summaryInterests = document.getElementById('summary-interests');

    if (summaryDest) summaryDest.textContent = planState.destinationName;
    if (summaryDays) {
      if (planState.mode === 'quick_visit') {
        summaryDays.textContent = `Quick Visit (${Math.round(planState.availableMinutes / 60)} Hours)`;
      } else {
        summaryDays.textContent = `${planState.durationDays} Days`;
      }
    }
    if (summaryWindow) {
      summaryWindow.textContent = `${planState.dailyStartTime} – ${planState.dailyEndTime}`;
    }
    if (summaryPace) summaryPace.textContent = planState.pace;
    if (summaryInterests) {
      summaryInterests.innerHTML = planState.interests.length > 0 
        ? planState.interests.map(i => `<span class="badge badge-primary">${i}</span>`).join(' ')
        : '<span class="text-muted">No preferences chosen</span>';
    }
  };

  // Generate Personalized Itinerary by calling the live DHRUVA backend engine
  const generateItinerary = async () => {
    const loadingOverlay = document.getElementById('planner-generating-overlay');
    if (loadingOverlay) {
      loadingOverlay.classList.add('active');
    }

    const cityId = planState.cityId || cityIdMap[planState.destinationId.toLowerCase()] || 1;

    // Build user interest weights (0.0 to 5.0)
    const interestWeights = {
      spiritual: planState.interests.includes('Spiritual') ? 5.0 : 2.5,
      architecture: planState.interests.includes('Architecture') ? 4.8 : 2.5,
      history: planState.interests.includes('Heritage') ? 4.5 : 2.5,
      culture: planState.interests.includes('Local Culture') ? 4.5 : 2.5,
      nature: planState.interests.includes('Nature') ? 4.0 : 2.0
    };

    const isSenior = planState.travelGroup.toLowerCase().includes('senior') || planState.pace.includes('Comfortable');

    // Build request payload for backend itinerary planning
    const payload = {
      destination: planState.destinationName,
      city_id: cityId,
      mode: planState.mode,
      num_days: planState.mode === 'quick_visit' ? 1 : planState.durationDays,
      start_date: planState.startDate || new Date().toISOString().split('T')[0],
      start_time: planState.dailyStartTime,
      end_time: planState.dailyEndTime,
      available_minutes: planState.availableMinutes,
      age: isSenior ? 58 : 35,
      pacing: planState.pace.toLowerCase().includes('comfort') ? 'relaxed' : 'balanced',
      interests: interestWeights,
      mandatory_place_ids: planState.mandatoryPlaceIds || []
    };

    try {
      const res = await DhruvaApp.apiPost('/api/itinerary/plan', payload);

      if (res.ok && res.data && res.data.status === 'success') {
        const planData = res.data;
        const dest = destinationsData.find(d => d.id === planState.destinationId) || destinationsData[0];
        
        const generatedPlan = {
          id: planData.trip_id ? `trip-${planData.trip_id}` : `plan-${Date.now()}`,
          tripId: planData.trip_id || null,
          destinationId: planState.destinationId,
          destinationName: planState.destinationName,
          startDate: planState.startDate,
          durationDays: planData.days ? planData.days.length : planState.durationDays,
          pace: planState.pace,
          interests: planState.interests,
          seniorFriendly: planData.senior_friendly,
          title: planData.title || `Cultural Journey in ${planState.destinationName}`,
          tagline: `${planData.days ? planData.days.length : planState.durationDays} Days of Heritage, Architecture & Sacred Traditions`,
          heroImage: dest ? dest.heroImage : 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173',
          days: (planData.days || []).map(day => {
            const rawItems = day.activities || day.items || day.itinerary_items || [];
            return {
              dayNumber: day.day_number,
              theme: day.theme,
              dateLabel: `Day 0${day.day_number}`,
              schedule: rawItems.map(it => {
                const arrPart = it.arrival_time ? (it.arrival_time.includes(' ') ? it.arrival_time.split(' ')[1] : it.arrival_time) : '';
                const isMorning = arrPart && (parseInt(arrPart.split(':')[0], 10) < 12 || arrPart.includes('AM'));
                return {
                  timeSlot: it.time_slot || `${it.arrival_time} - ${it.departure_time}`,
                  period: isMorning ? 'Morning' : 'Afternoon',
                  placeId: it.place_id,
                  title: it.place_name || it.name,
                  activity: it.description || `Visit ${it.place_name || it.name} and experience sacred living heritage.`,
                  duration: it.duration_hours ? `${it.duration_hours} Hours (${it.duration_minutes} Mins)` : `${it.duration_minutes || 60} Mins`,
                  culturalNote: it.category ? `${it.category} • ${it.cultural_tip || 'Sacred heritage sanctum'}` : (it.cultural_tip || 'Heritage Sanctum'),
                  transition: it.travel_time_from_prev_minutes ? `${it.travel_time_from_prev_minutes} min transit (${it.travel_distance_km} km)` : 'Transit to destination',
                  practicalTip: it.cultural_tip || 'Dress modestly and follow sanctum guidelines.',
                  isMandatory: it.is_mandatory || false
                };
              })
            };
          })
        };

        DhruvaApp.saveGeneratedPlan(generatedPlan);
        window.location.href = `itinerary.html?planId=${generatedPlan.id}&tripId=${planData.trip_id || ''}&dest=${planState.destinationId}`;
        return;
      } else if (res.status === 409 || (res.data && res.data.status === 'conflict')) {
        if (loadingOverlay) loadingOverlay.classList.remove('active');
        const conflict = res.data.conflict || res.data;
        alert(
          `⚠️ Time Constraint Conflict\n\n` +
          `The selected mandatory places require at least ${conflict.required_minutes || 'more'} minutes, but only ${conflict.available_minutes || 'limited'} minutes are available in this window.\n\n` +
          `Deficit: ${conflict.deficit_minutes || ''} minutes.\n` +
          `Recommendation: ${conflict.recommendation || 'Please expand your daily exploration window or remove a mandatory place.'}`
        );
        return;
      } else {
        throw new Error(res.data?.error || 'Failed to generate itinerary with live backend');
      }
    } catch (apiErr) {
      console.warn('Backend plan API call failed; synthesizing fallback itinerary:', apiErr);

      // Fallback synthesis from places respecting user start/end times
      const destPlaces = currentCityPlaces.length > 0 ? currentCityPlaces : placesData.filter(p => p.destinationId === planState.destinationId);
      const dest = destinationsData.find(d => d.id === planState.destinationId);

      const days = [];
      const daysCount = planState.mode === 'quick_visit' ? 1 : planState.durationDays;
      const startTime = planState.dailyStartTime || '10:30 AM';
      const endTime = planState.dailyEndTime || '07:30 PM';

      for (let d = 1; d <= daysCount; d++) {
        const morningPlace = destPlaces[(d - 1) * 2 % Math.max(1, destPlaces.length)] || destPlaces[0];
        const afternoonPlace = destPlaces[((d - 1) * 2 + 1) % Math.max(1, destPlaces.length)] || destPlaces[0];

        days.push({
          dayNumber: d,
          theme: `Day ${d}: Cultural Exploration of ${dest ? dest.name : 'Heritage Sites'}`,
          dateLabel: `Day 0${d}`,
          schedule: [
            {
              timeSlot: `${startTime} - 01:30 PM`,
              period: startTime.includes('AM') ? "Morning" : "Afternoon",
              placeId: morningPlace ? morningPlace.id : null,
              title: morningPlace ? morningPlace.name : "Heritage Morning Visit",
              activity: morningPlace ? (morningPlace.shortDescription || morningPlace.description) : "Explore iconic cultural quarter.",
              duration: "2.5 Hours",
              culturalNote: morningPlace ? (morningPlace.culturalSignificance || morningPlace.subCategory) : "Ancient living heritage site.",
              transition: "15 min comfortable ride.",
              practicalTip: "Enjoy comfortable temperatures during this time window."
            },
            {
              timeSlot: `03:30 PM - ${endTime}`,
              period: "Afternoon",
              placeId: afternoonPlace ? afternoonPlace.id : null,
              title: afternoonPlace ? afternoonPlace.name : "Cultural Exploration",
              activity: afternoonPlace ? (afternoonPlace.shortDescription || afternoonPlace.description) : "Experience traditional temple architecture.",
              duration: "2.5 Hours",
              culturalNote: "Preserving sacred Kalinga traditions.",
              transition: "Evening tea and relaxation.",
              practicalTip: "Wear comfortable walking footwear."
            }
          ]
        });
      }

      const generatedPlan = {
        id: `plan-${Date.now()}`,
        destinationId: planState.destinationId,
        destinationName: planState.destinationName,
        startDate: planState.startDate,
        durationDays: daysCount,
        pace: planState.pace,
        interests: planState.interests,
        title: `Cultural Journey in ${planState.destinationName}`,
        tagline: `${daysCount} Days of Heritage, Philosophy & Architecture`,
        heroImage: dest ? dest.heroImage : 'https://s7ap1.scene7.com/is/image/incredibleindia/lingaraj-temple-bhubaneshwar-odisha-1-attr-hero?qlt=82&ts=1742165306173',
        days: days
      };

      DhruvaApp.saveGeneratedPlan(generatedPlan);
      window.location.href = `itinerary.html?planId=${generatedPlan.id}&dest=${planState.destinationId}`;
    }
  };

  return {
    init,
    selectDestination,
    setTripMode,
    setQuickMinutes,
    setCustomDays,
    adjustDays,
    setCustomHours,
    adjustHours,
    setTimeWindow,
    toggleMandatoryPlace
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('planner-step-1')) {
    DhruvaPlanner.init();
  }
});

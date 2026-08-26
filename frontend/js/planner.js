/**
 * DHRUVA - Guided Trip Planner Logic
 * Multi-Step Conversational Planner & Dynamic Itinerary Synthesizer
 */

const DhruvaPlanner = (() => {
  let currentStep = 1;
  const totalSteps = 4;

  const planState = {
    destinationId: 'varanasi',
    destinationName: 'Varanasi',
    startDate: '',
    endDate: '',
    durationDays: 3,
    pace: 'Comfortable & Mindful',
    dailyStartTime: '08:00 AM',
    dailyEndTime: '08:00 PM',
    interests: ['Heritage', 'Spiritual', 'Local Culture'],
    travelGroup: 'Solo / Senior Friendly'
  };

  let destinationsData = [];
  let placesData = [];
  let itinerariesData = [];

  const init = async () => {
    // Load datasets
    destinationsData = await DhruvaApp.fetchMockData('destinations.json');
    placesData = await DhruvaApp.fetchMockData('places.json');
    itinerariesData = await DhruvaApp.fetchMockData('itineraries.json');

    // Parse URL params for pre-selection (e.g., ?dest=hampi)
    const urlParams = new URLSearchParams(window.location.search);
    const destParam = urlParams.get('dest');
    if (destParam && destinationsData.some(d => d.id === destParam)) {
      planState.destinationId = destParam;
      const found = destinationsData.find(d => d.id === destParam);
      planState.destinationName = found.name;
    }

    renderDestinationSelector();
    setupEventListeners();
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
            <span class="planner-dest-region">${dest.region} • ${dest.state}</span>
            <span class="badge badge-primary" style="margin-top: 4px;">Best: ${dest.bestTime.idealMonths}</span>
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
    }
    
    document.querySelectorAll('.planner-dest-option').forEach(el => {
      el.classList.toggle('selected', el.dataset.destId === destId);
    });

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
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('[data-duration-days]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        planState.durationDays = parseInt(btn.dataset.durationDays, 10);
        updateLiveSummary();
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
      // Set default tomorrow
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      dateInput.valueAsDate = tomorrow;
      planState.startDate = dateInput.value;

      dateInput.addEventListener('change', (e) => {
        planState.startDate = e.target.value;
        updateLiveSummary();
      });
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
    const summaryPace = document.getElementById('summary-pace');
    const summaryInterests = document.getElementById('summary-interests');

    if (summaryDest) summaryDest.textContent = planState.destinationName;
    if (summaryDays) summaryDays.textContent = `${planState.durationDays} Days`;
    if (summaryPace) summaryPace.textContent = planState.pace;
    if (summaryInterests) {
      summaryInterests.innerHTML = planState.interests.length > 0 
        ? planState.interests.map(i => `<span class="badge badge-primary">${i}</span>`).join(' ')
        : '<span class="text-muted">No preferences chosen</span>';
    }
  };

  // Generate Personalized Itinerary and Transition
  const generateItinerary = () => {
    // Show Loading Modal with cultural quote
    const loadingOverlay = document.getElementById('planner-generating-overlay');
    if (loadingOverlay) {
      loadingOverlay.classList.add('active');
    }

    setTimeout(() => {
      // Find or build appropriate itinerary
      let matchedItin = itinerariesData.find(itin => itin.destinationId === planState.destinationId);
      
      let generatedPlan;
      if (matchedItin) {
        generatedPlan = {
          id: `plan-${Date.now()}`,
          destinationId: planState.destinationId,
          destinationName: planState.destinationName,
          startDate: planState.startDate,
          durationDays: planState.durationDays,
          pace: planState.pace,
          interests: planState.interests,
          title: matchedItin.title,
          tagline: matchedItin.tagline,
          heroImage: matchedItin.heroImage,
          days: matchedItin.days.slice(0, planState.durationDays)
        };
      } else {
        // Synthesize dynamic plan from places
        const destPlaces = placesData.filter(p => p.destinationId === planState.destinationId);
        const dest = destinationsData.find(d => d.id === planState.destinationId);
        
        const days = [];
        for (let d = 1; d <= planState.durationDays; d++) {
          const morningPlace = destPlaces[(d - 1) * 2 % destPlaces.length] || destPlaces[0];
          const afternoonPlace = destPlaces[((d - 1) * 2 + 1) % destPlaces.length] || destPlaces[0];
          
          days.push({
            dayNumber: d,
            theme: `Day ${d}: Cultural Exploration of ${dest ? dest.name : 'Heritage Sites'}`,
            dateLabel: `Day ${d}`,
            schedule: [
              {
                timeSlot: "08:30 AM - 11:30 AM",
                period: "Morning",
                placeId: morningPlace ? morningPlace.id : null,
                title: morningPlace ? morningPlace.name : "Heritage Morning Walk",
                activity: morningPlace ? morningPlace.shortDescription : "Explore iconic cultural quarter.",
                duration: "3 Hours",
                culturalNote: morningPlace ? morningPlace.culturalSignificance : "Ancient living heritage site.",
                transition: "15 min comfortable ride.",
                practicalTip: "Morning hours provide the softest photography light."
              },
              {
                timeSlot: "03:30 PM - 06:30 PM",
                period: "Afternoon",
                placeId: afternoonPlace ? afternoonPlace.id : null,
                title: afternoonPlace ? afternoonPlace.name : "Cultural Artisanal Tour",
                activity: afternoonPlace ? afternoonPlace.shortDescription : "Experience traditional crafts and architecture.",
                duration: "3 Hours",
                culturalNote: "Preserving multi-generational craft and spiritual lineages.",
                transition: "Evening tea at traditional haveli cafe.",
                practicalTip: "Wear comfortable walking footwear."
              }
            ]
          });
        }

        generatedPlan = {
          id: `plan-${Date.now()}`,
          destinationId: planState.destinationId,
          destinationName: planState.destinationName,
          startDate: planState.startDate,
          durationDays: planState.durationDays,
          pace: planState.pace,
          interests: planState.interests,
          title: `Cultural Journey in ${planState.destinationName}`,
          tagline: `${planState.durationDays} Days of Heritage, Philosophy & Architecture`,
          heroImage: dest ? dest.heroImage : 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80',
          days: days
        };
      }

      // Save plan in localStorage
      DhruvaApp.saveGeneratedPlan(generatedPlan);

      // Redirect to itinerary page
      window.location.href = `itinerary.html?planId=${generatedPlan.id}&dest=${planState.destinationId}`;
    }, 1800);
  };

  return {
    init,
    selectDestination
  };
})();

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('planner-step-1')) {
    DhruvaPlanner.init();
  }
});

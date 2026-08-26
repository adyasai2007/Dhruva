/**
 * DHRUVA - ChatGPT-Style Interactive Voice Orb Assistant
 * With Real-Time Vocal Pitch Detection (Autocorrelation Algorithm),
 * Live Audio-Reactive Fluid Canvas Engine, Web Speech Recognition (STT),
 * and Speech Synthesis (TTS).
 */

const DhruvaVoiceOrb = (() => {
  let isInitialized = false;
  let isOpen = false;
  let isMuted = false;
  let audioContext = null;
  let analyser = null;
  let microphone = null;
  let timeDomainBuffer = null;
  let frequencyBuffer = null;
  let animationFrameId = null;

  let recognition = null;
  let isRecognizing = false;
  let assistantState = 'idle'; // 'idle' | 'listening' | 'thinking' | 'speaking'
  
  // Real-time Audio Metrics
  let currentVolume = 0;
  let smoothedVolume = 0;
  let currentPitchHz = 0;
  let smoothedPitchHz = 160;
  let normalizedPitch = 0.3; // 0.0 (deep bass) to 1.0 (high soprano)
  let pitchRegister = 'Mid';

  // DOM Elements
  let overlayEl = null;
  let canvasEl = null;
  let ctx = null;
  let stateLabelEl = null;
  let pitchBadgeEl = null;
  let transcriptEl = null;
  let responseEl = null;
  let micBtnEl = null;
  let permWarningEl = null;

  // Knowledge base for conversational local guidance
  const culturalResponses = [
    {
      keywords: ['varanasi', 'kashi', 'banaras', 'ganga', 'aarti'],
      reply: "Varanasi is the timeless spiritual heart of India. I can guide you through the sunrise Subah-e-Banaras boat ride, Kashi Vishwanath temple corridor, and evening Ganga Aarti.",
      actionUrl: 'trip.html?dest=varanasi'
    },
    {
      keywords: ['hampi', 'ruins', 'vijayanagara', 'stone chariot'],
      reply: "Hampi is an extraordinary open-air granite museum. Would you like to explore the 14th-century Vijaya Vittala temple and coracle river crossing?",
      actionUrl: 'trip.html?dest=hampi'
    },
    {
      keywords: ['jaipur', 'pink city', 'amer', 'fort', 'hawa mahal', 'rajasthan'],
      reply: "Jaipur showcases regal Rajput palaces and vibrant bazaars. Let's plan your visit to Amer Fort, Sheesh Mahal, and block-printing workshops.",
      actionUrl: 'trip.html?dest=jaipur'
    },
    {
      keywords: ['madurai', 'meenakshi', 'tamil', 'temple'],
      reply: "Madurai is ancient Tamil civilization's crown with the magnificent 14 sculpted gopurams of Meenakshi Amman Temple.",
      actionUrl: 'trip.html?dest=madurai'
    },
    {
      keywords: ['kolkata', 'durga puja', 'victoria memorial', 'calcutta', 'bengal'],
      reply: "Kolkata represents India's intellectual renaissance, terracotta craftsmanship, and vibrant culinary heritage.",
      actionUrl: 'trip.html?dest=kolkata'
    },
    {
      keywords: ['best time', 'season', 'weather', 'when to visit'],
      reply: "The ideal visiting window across most of India is October through March, offering crisp sunshine and pleasant morning ghat walks.",
      actionUrl: 'explore.html?section=best-time'
    },
    {
      keywords: ['explore', 'places', 'monuments', 'destinations'],
      reply: "Opening DHRUVA's cultural directory featuring heritage capitals across North, South, East, and West India.",
      actionUrl: 'explore.html'
    },
    {
      keywords: ['plan', 'itinerary', 'trip', 'generate'],
      reply: "Let's craft your personalized journey. Starting the conversational trip planner.",
      actionUrl: 'trip.html'
    }
  ];

  // Initialize UI & Bindings
  const init = () => {
    if (isInitialized) return;
    injectVoiceOverlay();
    bindGlobalButtons();
    initSpeechRecognition();
    isInitialized = true;
  };

  // Inject ChatGPT-Style Voice Overlay Markup
  const injectVoiceOverlay = () => {
    let existing = document.getElementById('dhruva-voice-orb-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'dhruva-voice-orb-overlay';
    overlay.className = 'voice-orb-overlay';
    overlay.innerHTML = `
      <div class="voice-orb-perm-warning" id="voice-perm-warning">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span>Microphone access needed for live voice & pitch tracking. Tap the mic button to grant permission.</span>
      </div>

      <header class="voice-orb-header">
        <div class="voice-orb-brand">
          <svg class="voice-orb-brand-star" viewBox="0 0 32 32">
            <path d="M16 2 L19 12 L29 12 L21 18 L24 28 L16 22 L8 28 L11 18 L3 12 L13 12 Z" />
          </svg>
          <span class="voice-orb-title">DHRUVA VOICE GUIDE</span>
        </div>
        <button class="voice-orb-close-btn" id="voice-close-btn" aria-label="Close voice assistant">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </header>

      <!-- Central Animated Voice Orb -->
      <div class="voice-orb-stage">
        <div class="voice-orb-canvas-wrapper">
          <div class="voice-orb-glow-backdrop" id="voice-glow-backdrop"></div>
          <canvas id="voice-orb-canvas" class="voice-orb-canvas" width="200" height="200"></canvas>
        </div>

        <div class="voice-orb-status-box">
          <div class="voice-orb-state-label" id="voice-state-label">
            <span class="voice-orb-state-dot"></span>
            <span id="voice-state-text">Ready • Tap to Speak</span>
          </div>

          <!-- Live Vocal Pitch Indicator Badge -->
          <div>
            <span class="voice-orb-pitch-badge" id="voice-pitch-badge">
              <span class="voice-orb-pitch-dot"></span>
              <span id="voice-pitch-text">🎵 Pitch: Listening...</span>
            </span>
          </div>

          <div class="voice-orb-transcript" id="voice-transcript">"Speak or hum your destination or question..."</div>
          <div class="voice-orb-response" id="voice-response"></div>
        </div>

        <div class="voice-orb-suggestions">
          <button class="voice-orb-suggestion-pill" data-query="Plan a spiritual trip to Varanasi">"Spiritual trip to Varanasi"</button>
          <button class="voice-orb-suggestion-pill" data-query="Explore UNESCO monuments in Hampi">"Monuments of Hampi"</button>
          <button class="voice-orb-suggestion-pill" data-query="Best time to visit Jaipur">"Best time for Jaipur"</button>
        </div>
      </div>

      <!-- Bottom Voice Controls -->
      <div class="voice-orb-controls">
        <button class="voice-orb-action-btn btn-secondary-action" id="voice-refresh-btn" title="Clear conversation" aria-label="Clear conversation">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><polyline points="23 20 23 14 17 14"></polyline><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path></svg>
        </button>

        <button class="voice-orb-action-btn btn-mic" id="voice-mic-btn" title="Toggle microphone" aria-label="Toggle microphone">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        </button>

        <button class="voice-orb-action-btn btn-secondary-action" id="voice-end-btn" title="End Session" aria-label="End Session">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><rect x="9" y="9" width="6" height="6"></rect></svg>
        </button>
      </div>
    `;

    document.body.appendChild(overlay);

    overlayEl = overlay;
    canvasEl = document.getElementById('voice-orb-canvas');
    ctx = canvasEl.getContext('2d');
    stateLabelEl = document.getElementById('voice-state-text');
    pitchBadgeEl = document.getElementById('voice-pitch-text');
    transcriptEl = document.getElementById('voice-transcript');
    responseEl = document.getElementById('voice-response');
    micBtnEl = document.getElementById('voice-mic-btn');
    permWarningEl = document.getElementById('voice-perm-warning');

    // Attach internal button events
    document.getElementById('voice-close-btn').addEventListener('click', close);
    document.getElementById('voice-end-btn').addEventListener('click', close);
    document.getElementById('voice-refresh-btn').addEventListener('click', resetConversation);
    micBtnEl.addEventListener('click', toggleMicrophone);

    // Suggestion pills
    overlay.querySelectorAll('.voice-orb-suggestion-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        handleUserInput(pill.dataset.query);
      });
    });
  };

  // Bind any open-voice buttons across all pages
  const bindGlobalButtons = () => {
    document.querySelectorAll('[data-action="open-voice"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        open();
      });
    });
  };

  // Open the Voice Orb
  const open = async () => {
    if (!overlayEl) injectVoiceOverlay();
    isOpen = true;
    overlayEl.classList.add('active');

    // Start Orb rendering loop
    startOrbRenderLoop();

    // Start Live Microphone Access & Speech Recognition
    await startMicrophone();
    startRecognition();
  };

  // Close the Voice Orb
  const close = () => {
    isOpen = false;
    if (overlayEl) overlayEl.classList.remove('active');
    
    stopRecognition();
    stopMicrophone();
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
  };

  // Reset conversation
  const resetConversation = () => {
    transcriptEl.textContent = '"Speak or hum your destination or question..."';
    responseEl.textContent = '';
    setAssistantState('listening');
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  };

  // Update Assistant State
  const setAssistantState = (state, text = null) => {
    assistantState = state;
    if (!overlayEl) return;

    overlayEl.classList.remove('listening', 'thinking', 'speaking', 'idle');
    overlayEl.classList.add(state);

    const labels = {
      idle: 'Tap to Speak',
      listening: 'Listening to your voice...',
      thinking: 'Dhruva is thinking...',
      speaking: 'Dhruva is speaking...'
    };

    if (stateLabelEl) {
      stateLabelEl.textContent = text || labels[state] || 'Ready';
    }
  };

  // Start Real Microphone via Web Audio API
  const startMicrophone = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not supported in this browser environment');
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048; // High resolution for pitch autocorrelation
      analyser.smoothingTimeConstant = 0.8;

      microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);

      timeDomainBuffer = new Float32Array(analyser.fftSize);
      frequencyBuffer = new Uint8Array(analyser.frequencyBinCount);

      if (permWarningEl) permWarningEl.classList.remove('show');
      setAssistantState('listening');
    } catch (err) {
      console.warn('Microphone access not granted or unavailable:', err);
      if (permWarningEl) permWarningEl.classList.add('show');
      setAssistantState('idle', 'Microphone Ready (Tap to Speak)');
    }
  };

  // Stop Microphone
  const stopMicrophone = () => {
    if (microphone && microphone.mediaStream) {
      microphone.mediaStream.getTracks().forEach(track => track.stop());
    }
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close();
    }
    audioContext = null;
    microphone = null;
    analyser = null;
  };

  // Toggle Microphone Mute
  const toggleMicrophone = () => {
    isMuted = !isMuted;
    micBtnEl.classList.toggle('muted', isMuted);
    if (isMuted) {
      stopRecognition();
      setAssistantState('idle', 'Microphone Muted');
      if (pitchBadgeEl) pitchBadgeEl.textContent = '🎵 Muted';
    } else {
      startRecognition();
      setAssistantState('listening');
    }
  };

  // High-Precision Autocorrelation Pitch Detection Algorithm
  const detectPitchFromBuffer = (buffer, sampleRate) => {
    let size = buffer.length;
    let rms = 0;

    // Calculate Root Mean Square (RMS) volume
    for (let i = 0; i < size; i++) {
      let val = buffer[i];
      rms += val * val;
    }
    rms = Math.sqrt(rms / size);

    // If signal is too quiet / background noise, return no pitch
    if (rms < 0.015) {
      return { pitchHz: 0, confidence: 0, rms };
    }

    // Autocorrelation Search Range (min 65Hz to max 1000Hz)
    let minPeriod = Math.floor(sampleRate / 1000); // ~44 samples at 44.1kHz
    let maxPeriod = Math.floor(sampleRate / 65);   // ~680 samples at 44.1kHz

    let bestCorrelation = 0;
    let bestPeriod = -1;
    let correlations = new Float32Array(maxPeriod + 1);

    for (let period = minPeriod; period <= maxPeriod; period++) {
      let sum = 0;
      for (let i = 0; i < size - period; i++) {
        sum += buffer[i] * buffer[i + period];
      }
      correlations[period] = sum;

      if (sum > bestCorrelation) {
        bestCorrelation = sum;
        bestPeriod = period;
      }
    }

    // Parabolic Interpolation for Sub-Sample Peak Pitch Accuracy
    if (bestPeriod > minPeriod && bestPeriod < maxPeriod) {
      let alpha = correlations[bestPeriod - 1];
      let beta = correlations[bestPeriod];
      let gamma = correlations[bestPeriod + 1];
      let delta = (alpha - gamma) / (2 * (alpha - 2 * beta + gamma));
      let exactPeriod = bestPeriod + delta;
      let pitchHz = sampleRate / exactPeriod;

      let confidence = bestCorrelation / (rms * rms * size);
      return { pitchHz, confidence, rms };
    }

    return { pitchHz: 0, confidence: 0, rms };
  };

  // Web Speech Recognition (Speech-to-Text)
  const initSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.info('SpeechRecognition API not available in this browser; fallback mode active.');
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      const text = final || interim;
      if (text && transcriptEl) {
        transcriptEl.textContent = `"${text}"`;
      }

      if (final) {
        handleUserInput(final);
      }
    };

    recognition.onerror = (e) => {
      if (e.error !== 'no-speech') {
        console.warn('Speech recognition status:', e.error);
      }
    };

    recognition.onend = () => {
      if (isOpen && !isMuted && isRecognizing) {
        try { recognition.start(); } catch (e) {}
      }
    };
  };

  const startRecognition = () => {
    if (recognition && !isRecognizing) {
      try {
        recognition.start();
        isRecognizing = true;
      } catch (e) {}
    }
  };

  const stopRecognition = () => {
    if (recognition && isRecognizing) {
      try {
        recognition.stop();
        isRecognizing = false;
      } catch (e) {}
    }
  };

  // Process User Input & Respond
  const handleUserInput = (inputText) => {
    if (!inputText || !inputText.trim()) return;

    setAssistantState('thinking');
    transcriptEl.textContent = `"${inputText}"`;

    setTimeout(() => {
      const lower = inputText.toLowerCase();
      let matched = culturalResponses.find(item => 
        item.keywords.some(k => lower.includes(k))
      );

      if (!matched) {
        matched = {
          reply: `I heard "${inputText}". DHRUVA can guide you to explore sacred temples, ancient forts, or synthesize a customized multi-day cultural plan.`,
          actionUrl: 'pages/explore.html'
        };
      }

      responseEl.textContent = matched.reply;
      speakResponse(matched.reply, matched.actionUrl);
    }, 700);
  };

  // Text-to-Speech Vocalization
  const speakResponse = (text, redirectUrl = null) => {
    setAssistantState('speaking');

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.05;

      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang.includes('en-IN') || v.name.includes('India') || v.name.includes('Natural') || v.lang.includes('en-GB'));
      if (preferredVoice) utterance.voice = preferredVoice;

      utterance.onend = () => {
        setAssistantState('listening');
        if (redirectUrl) {
          setTimeout(() => {
            close();
            const target = redirectUrl.startsWith('pages/') ? redirectUrl : (window.location.pathname.includes('/pages/') ? redirectUrl.replace('pages/', '') : `pages/${redirectUrl}`);
            window.location.href = target;
          }, 1000);
        }
      };

      utterance.onerror = () => {
        setAssistantState('listening');
      };

      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => {
        setAssistantState('listening');
        if (redirectUrl) {
          close();
          window.location.href = window.location.pathname.includes('/pages/') ? redirectUrl.replace('pages/', '') : `pages/${redirectUrl}`;
        }
      }, 3500);
    }
  };

  // ChatGPT-Style Pitch-Reactive Canvas Orb Engine (Silky Smooth & Aesthetic)
  let time = 0;
  const startOrbRenderLoop = () => {
    if (!canvasEl || !ctx) return;

    const render = () => {
      if (!isOpen) return;

      // Gentle, calm time progression
      time += 0.016;

      let audioEnergy = 0;

      // Real-time live audio processing
      if (analyser && timeDomainBuffer && !isMuted) {
        analyser.getFloatTimeDomainData(timeDomainBuffer);
        const pitchData = detectPitchFromBuffer(timeDomainBuffer, audioContext.sampleRate);

        audioEnergy = pitchData.rms * 2.8; // Gentle energy scaling

        if (pitchData.pitchHz > 60 && pitchData.pitchHz < 900) {
          currentPitchHz = pitchData.pitchHz;
          // Smooth damping to eliminate jitter
          smoothedPitchHz += (currentPitchHz - smoothedPitchHz) * 0.09;

          // Normalized Pitch: 80Hz (Bass = 0.0) to 480Hz (High = 1.0)
          normalizedPitch += ((Math.min(Math.max((smoothedPitchHz - 80) / 400, 0), 1)) - normalizedPitch) * 0.08;

          if (smoothedPitchHz < 145) {
            pitchRegister = 'Deep Bass';
          } else if (smoothedPitchHz < 275) {
            pitchRegister = 'Warm Mid';
          } else {
            pitchRegister = 'High Register';
          }

          if (pitchBadgeEl) {
            pitchBadgeEl.textContent = `🎵 Pitch: ${Math.round(smoothedPitchHz)} Hz • ${pitchRegister}`;
          }
        } else if (audioEnergy < 0.035) {
          if (pitchBadgeEl && assistantState === 'listening') {
            pitchBadgeEl.textContent = `🎵 Speak or Hum into Mic`;
          }
        }
      } else if (assistantState === 'speaking') {
        audioEnergy = 0.35 + 0.2 * Math.sin(time * 3.5) * Math.cos(time * 1.8);
        smoothedPitchHz += (210 + 40 * Math.sin(time * 2) - smoothedPitchHz) * 0.08;
        normalizedPitch += (0.35 - normalizedPitch) * 0.08;
        if (pitchBadgeEl) pitchBadgeEl.textContent = `🎵 Dhruva Speaking`;
      } else if (assistantState === 'thinking') {
        audioEnergy = 0.18 + 0.08 * Math.sin(time * 4);
        normalizedPitch += (0.5 - normalizedPitch) * 0.08;
        if (pitchBadgeEl) pitchBadgeEl.textContent = `🎵 Synthesizing...`;
      } else {
        // Idle calming breath
        audioEnergy = 0.05 + 0.02 * Math.sin(time * 1.2);
        if (pitchBadgeEl) pitchBadgeEl.textContent = `🎵 Ready • Tap to Speak`;
      }

      // Buttery smooth volume damping
      smoothedVolume += (audioEnergy - smoothedVolume) * 0.08;

      const width = canvasEl.width;
      const height = canvasEl.height;
      const centerX = width / 2;
      const centerY = height / 2;

      // Base radius with pleasant breathing scale for compact corner canvas
      const baseRadius = 45 + smoothedVolume * 20;

      ctx.clearRect(0, 0, width, height);
      ctx.save();

      // Multi-layer Organic Fluid Silk Rings
      const numLayers = 4;
      for (let layer = numLayers; layer >= 1; layer--) {
        ctx.beginPath();
        const layerRadius = baseRadius * (0.65 + layer * 0.22);
        const points = 64; // High resolution vertex circle for ultra smoothness

        for (let i = 0; i <= points; i++) {
          const angle = (i / points) * Math.PI * 2;
          
          // Harmonic superposition creating aesthetic silk-like fluid flow
          const h1 = Math.sin(angle * 2 + time * 1.2 + layer * 0.6) * 0.55;
          const h2 = Math.sin(angle * 3 - time * 0.8 + layer * 0.9) * 0.35;
          const h3 = Math.sin(angle * (3 + Math.round(normalizedPitch * 3)) + time * 1.6) * (0.2 + normalizedPitch * 0.3);
          
          const totalDistortion = (h1 + h2 + h3);
          const rippleAmplitude = (8 + smoothedVolume * 18) * (0.7 + normalizedPitch * 0.5);
          const r = layerRadius + totalDistortion * rippleAmplitude;
          
          const x = centerX + Math.cos(angle) * r;
          const y = centerY + Math.sin(angle) * r;

          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }

        ctx.closePath();

        // Soft, calmed color gradients
        const grad = ctx.createRadialGradient(
          centerX - 8 * Math.sin(time * 0.8),
          centerY - 8 * Math.cos(time * 0.8),
          6,
          centerX,
          centerY,
          layerRadius * 1.25
        );

        if (normalizedPitch > 0.65) {
          // High Pitch: Ethereal champagne gold & warm solar glow
          grad.addColorStop(0, `rgba(255, 252, 240, ${0.72 / layer})`);
          grad.addColorStop(0.35, `rgba(224, 182, 90, ${0.50 / layer})`);
          grad.addColorStop(0.70, `rgba(185, 130, 45, ${0.30 / layer})`);
          grad.addColorStop(1, `rgba(35, 74, 53, 0)`);
        } else if (normalizedPitch > 0.3) {
          // Mid Pitch: Dhruva signature pearl green & antique gold
          grad.addColorStop(0, `rgba(255, 253, 248, ${0.75 / layer})`);
          grad.addColorStop(0.35, `rgba(185, 154, 91, ${0.48 / layer})`);
          grad.addColorStop(0.75, `rgba(35, 74, 53, ${0.30 / layer})`);
          grad.addColorStop(1, `rgba(23, 53, 37, 0)`);
        } else {
          // Deep Bass Pitch: Soft earthy jade & gentle bronze
          grad.addColorStop(0, `rgba(235, 242, 233, ${0.68 / layer})`);
          grad.addColorStop(0.40, `rgba(71, 113, 77, ${0.48 / layer})`);
          grad.addColorStop(0.80, `rgba(23, 53, 37, ${0.32 / layer})`);
          grad.addColorStop(1, `rgba(13, 29, 20, 0)`);
        }

        ctx.fillStyle = grad;
        ctx.fill();
      }

      // Elegant Central Guiding Star Core (Calm and restrained)
      const starScale = (1 + smoothedVolume * 0.25);
      const starSpikes = 8;
      
      ctx.fillStyle = 'rgba(255, 253, 248, 0.92)';
      ctx.shadowColor = 'rgba(185, 154, 91, 0.5)';
      ctx.shadowBlur = 8 + smoothedVolume * 8;
      
      ctx.beginPath();
      for (let s = 0; s < starSpikes; s++) {
        const starAngle = (s / starSpikes) * Math.PI * 2 + time * 0.25;
        const starR = (s % 2 === 0 ? 12 : 5) * starScale;
        const sx = centerX + Math.cos(starAngle) * starR;
        const sy = centerY + Math.sin(starAngle) * starR;
        if (s === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      }
      ctx.closePath();
      ctx.fill();

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();
  };

  return {
    init,
    open,
    close,
    handleUserInput
  };
})();

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', DhruvaVoiceOrb.init);

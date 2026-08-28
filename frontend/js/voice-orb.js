/**
 * DHRUVA — Conversational & Navigational Voice Orb Assistant
 * Powered by Gemini Live Architecture.
 * Features:
 * - Real-Time Vocal Pitch Detection (Autocorrelation)
 * - Audio-Reactive Golden Halo Canvas Visualizer
 * - Real-time WebSocket Audio Streaming to Gemini Live API
 * - Full Backend Tool Execution & Dynamic Frontend UI Navigation
 */

const DhruvaVoiceOrb = (() => {
  let isInitialized = false;
  let isOpen = false;
  let isMuted = false;
  let audioContext = null; // for mic recording (16kHz)
  let playAudioContext = null; // for Gemini output (24kHz)
  let analyser = null;
  let microphone = null;
  let processor = null;
  let ws = null;
  let timeDomainBuffer = null;
  let animationFrameId = null;

  let assistantState = 'idle'; // 'idle' | 'listening' | 'thinking' | 'speaking'
  let nextPlayTime = 0;
  
  // Real-time Audio & Pitch Metrics
  let smoothedVolume = 0;
  let currentPitchHz = 0;
  let smoothedPitchHz = 160;
  let normalizedPitch = 0.35;
  let pitchRegister = 'Mid Register';

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

  // Initialize UI & Bindings
  const init = () => {
    if (isInitialized) return;
    injectVoiceOverlay();
    bindGlobalButtons();
    isInitialized = true;
  };

  // Inject Voice Guide Overlay HTML Markup
  const injectVoiceOverlay = () => {
    let existing = document.getElementById('dhruva-voice-orb-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'dhruva-voice-orb-overlay';
    overlay.className = 'voice-orb-overlay';
    overlay.innerHTML = `
      <div class="voice-orb-perm-warning" id="voice-perm-warning">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span>Microphone access required for voice conversation. Tap the microphone icon to grant access.</span>
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

      <!-- Central Animated Voice Stage -->
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

          <!-- Vocal Pitch Tracking Badge -->
          <div>
            <span class="voice-orb-pitch-badge" id="voice-pitch-badge">
              <span class="voice-orb-pitch-dot"></span>
              <span id="voice-pitch-text">🎵 Ready • Tap to Speak</span>
            </span>
          </div>

          <div class="voice-orb-transcript" id="voice-transcript">"Speak or hum your destination or question..."</div>
          <div class="voice-orb-response" id="voice-response"></div>
        </div>

        <!-- Quick Guidance Prompts -->
        <div class="voice-orb-suggestions">
          <button class="voice-orb-suggestion-pill" data-query="Plan a 3-day spiritual trip to Puri">"3-Day Spiritual Trip to Puri"</button>
          <button class="voice-orb-suggestion-pill" data-query="Explore temples of Bhubaneswar">"Temples of Bhubaneswar"</button>
          <button class="voice-orb-suggestion-pill" data-query="Tell me about Konark Sun Temple">"Monuments of Konark"</button>
          <button class="voice-orb-suggestion-pill" data-query="When are the festival dates for Rath Yatra in Puri?">"Festivals in Puri"</button>
        </div>
      </div>

      <!-- Bottom Voice Controls -->
      <div class="voice-orb-controls">
        <button class="voice-orb-action-btn btn-secondary-action" id="voice-refresh-btn" title="Reset conversation" aria-label="Reset conversation">
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

        <button class="voice-orb-action-btn btn-secondary-action" id="voice-end-btn" title="Close" aria-label="Close">
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

    // Attach listeners
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

  // Bind all microphone triggers across pages
  const bindGlobalButtons = () => {
    document.querySelectorAll('[data-action="open-voice"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        open();
      });
    });
  };

  // Open the Voice Guide
  const open = async () => {
    if (!overlayEl) injectVoiceOverlay();
    isOpen = true;
    overlayEl.classList.add('active');

    // Start Visualizer Loop
    startOrbRenderLoop();

    // Start Microphone & WebSocket
    await startMicrophone();
  };

  // Close the Voice Guide
  const close = () => {
    isOpen = false;
    if (overlayEl) overlayEl.classList.remove('active');
    
    stopMicrophone();
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
  };

  // Reset Conversation Context
  const resetConversation = () => {
    if (transcriptEl) transcriptEl.textContent = '"Speak or hum your destination or question..."';
    if (responseEl) responseEl.textContent = '';
    setAssistantState('listening', 'Listening to your voice...');
    stopMicrophone();
    setTimeout(() => startMicrophone(), 300);
  };

  // Set Assistant State
  const setAssistantState = (state, customText = null) => {
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
      stateLabelEl.textContent = customText || labels[state] || 'Ready';
    }
  };

  // Start Real Microphone via Web Audio API & Connect WebSocket
  const startMicrophone = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not supported in this browser');
      }

      // 1. Initialize Audio Contexts
      if (!audioContext || audioContext.state === 'closed') {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      }
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }

      if (!playAudioContext || playAudioContext.state === 'closed') {
        playAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
      }
      if (playAudioContext.state === 'suspended') {
        await playAudioContext.resume();
      }
      nextPlayTime = playAudioContext.currentTime;

      // 2. Request mic stream
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true
        }, 
        video: false 
      });

      // 3. Connect to Python WebSocket Backend
      const wsUrl = `ws://${window.location.hostname || 'localhost'}:8001`;
      ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer";

      ws.onopen = () => {
        console.log("WebSocket connected to Gemini Live Backend at", wsUrl);

        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;

        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);

        // 2048 samples = 128ms per chunk for responsive real-time streaming
        processor = audioContext.createScriptProcessor(2048, 1, 1);
        processor.onaudioprocess = (e) => {
            if (!ws || ws.readyState !== WebSocket.OPEN || isMuted) return;
            
            let inputData = e.inputBuffer.getChannelData(0);
            let pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                let s = Math.max(-1, Math.min(1, inputData[i]));
                pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            ws.send(pcm16.buffer);
        };

        microphone.connect(processor);
        processor.connect(audioContext.destination);
        timeDomainBuffer = new Float32Array(analyser.fftSize);

        if (permWarningEl) permWarningEl.classList.remove('show');
        setAssistantState('listening');
      };

      ws.onmessage = (event) => {
          if (event.data instanceof ArrayBuffer) {
              playAudioChunk(event.data);
          } else {
              try {
                  const data = JSON.parse(event.data);
                  handleBackendEvent(data);
              } catch (e) {
                  console.warn("Failed to parse backend message:", e);
              }
          }
      };

      ws.onerror = (e) => {
          console.warn("WebSocket error:", e);
      };

      ws.onclose = () => {
          console.log("WebSocket closed");
          if (isOpen) {
            setAssistantState('idle', 'Disconnected');
          }
      };
      
    } catch (err) {
      console.warn('Microphone access not granted or unavailable:', err);
      if (permWarningEl) permWarningEl.classList.add('show');
      setAssistantState('idle', 'Microphone Ready (Tap to Speak)');
    }
  };

  const playAudioChunk = (arrayBuffer) => {
      if (!playAudioContext || playAudioContext.state === 'closed') return;
      
      setAssistantState('speaking', 'Dhruva is speaking...');
      
      let pcmData = new Int16Array(arrayBuffer);
      let audioBuffer = playAudioContext.createBuffer(1, pcmData.length, 24000);
      let channelData = audioBuffer.getChannelData(0);
      
      for (let i = 0; i < pcmData.length; i++) {
          channelData[i] = pcmData[i] / 32768.0;
      }

      let source = playAudioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(playAudioContext.destination);

      // Prevent gap or drift if previous playback ended a while ago
      if (playAudioContext.currentTime > nextPlayTime + 0.3) {
          nextPlayTime = playAudioContext.currentTime;
      }

      let scheduleTime = Math.max(playAudioContext.currentTime, nextPlayTime);
      source.start(scheduleTime);
      nextPlayTime = scheduleTime + audioBuffer.duration;

      source.onended = () => {
          // If this is the last queued chunk, switch back to listening
          if (playAudioContext && playAudioContext.currentTime >= nextPlayTime - 0.08) {
              setAssistantState('listening');
          }
      };
  };

  const handleBackendEvent = (event) => {
      if (event.type === 'transcript') {
          if (event.role === 'user' && transcriptEl) {
              transcriptEl.textContent = `"${event.text}"`;
          } else if (event.role === 'gemini' && responseEl) {
              responseEl.textContent = event.text;
          }
      } else if (event.type === 'interrupted') {
          console.log("[Interrupted] Flushing audio buffer");
          if (playAudioContext) nextPlayTime = playAudioContext.currentTime;
      } else if (event.type === 'tool_call') {
          setAssistantState('thinking', `Executing ${event.name}...`);
      } else if (event.type === 'navigation') {
          handleVoiceNavigation(event.data);
      } else if (event.type === 'error') {
          if (responseEl) {
              responseEl.textContent = event.message.includes("quota") 
                  ? "Gemini Live API quota exceeded. Please wait a moment." 
                  : `Voice Error: ${event.message}`;
          }
      }
  };

  // Stop Microphone & WS
  const stopMicrophone = () => {
    if (processor) {
      try { processor.disconnect(); } catch (e) {}
    }
    if (microphone && microphone.mediaStream) {
      try { microphone.mediaStream.getTracks().forEach(track => track.stop()); } catch (e) {}
    }
    if (audioContext && audioContext.state !== 'closed') {
      try { audioContext.close(); } catch (e) {}
    }
    if (playAudioContext && playAudioContext.state !== 'closed') {
      try { playAudioContext.close(); } catch (e) {}
    }
    if (ws) {
      try { ws.close(); } catch (e) {}
    }
    
    audioContext = null;
    playAudioContext = null;
    microphone = null;
    analyser = null;
    processor = null;
    ws = null;
  };

  // Toggle Microphone Mute
  const toggleMicrophone = () => {
    isMuted = !isMuted;
    if (micBtnEl) micBtnEl.classList.toggle('muted', isMuted);
    if (isMuted) {
      setAssistantState('idle', 'Microphone Muted');
      if (pitchBadgeEl) pitchBadgeEl.textContent = '🎵 Muted';
    } else {
      setAssistantState('listening');
    }
  };

  // Autocorrelation Pitch Detection
  const detectPitchFromBuffer = (buffer, sampleRate) => {
    let size = buffer.length;
    let rms = 0;
    for (let i = 0; i < size; i++) {
      let val = buffer[i];
      rms += val * val;
    }
    rms = Math.sqrt(rms / size);
    if (rms < 0.015) return { pitchHz: 0, confidence: 0, rms };

    let minPeriod = Math.floor(sampleRate / 1000);
    let maxPeriod = Math.floor(sampleRate / 65);
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

    if (bestPeriod > minPeriod && bestPeriod < maxPeriod) {
      let alpha = correlations[bestPeriod - 1];
      let beta = correlations[bestPeriod];
      let gamma = correlations[bestPeriod + 1];
      let delta = (alpha - gamma) / (2 * (alpha - 2 * beta + gamma));
      let exactPeriod = bestPeriod + delta;
      let pitchHz = sampleRate / exactPeriod;
      return { pitchHz, confidence: bestCorrelation / correlations[0], rms };
    }
    return { pitchHz: 0, confidence: 0, rms };
  };

  // Process Quick Suggestion text through WebSocket
  const handleUserInput = (inputText) => {
    if (!inputText || !inputText.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    setAssistantState('thinking');
    if (transcriptEl) transcriptEl.textContent = `"${inputText}"`;
    ws.send(inputText);
  };

  // Handle Dynamic UI Navigation
  const handleVoiceNavigation = (navAction) => {
    if (!navAction) return;

    const isInsidePages = window.location.pathname.includes('/pages/');

    if (navAction.action === 'open_modal' && navAction.place) {
      setTimeout(() => {
        close();
        if (typeof DhruvaComponents !== 'undefined' && DhruvaComponents.openPlaceDetailsModal) {
          DhruvaComponents.openPlaceDetailsModal(navAction.place.id);
        }
      }, 1200);
      return;
    }

    let targetUrl = null;
    if (navAction.screen === 'itinerary' || navAction.action === 'view_itinerary') {
      targetUrl = isInsidePages ? 'itinerary.html' : 'pages/itinerary.html';
    } else if (navAction.screen === 'explore') {
      const qParams = navAction.query_params || {};
      const searchStr = new URLSearchParams(qParams).toString();
      targetUrl = (isInsidePages ? 'explore.html' : 'pages/explore.html') + (searchStr ? '?' + searchStr : '');
    } else if (navAction.screen === 'trip_planner' || navAction.screen === 'trip') {
      targetUrl = isInsidePages ? 'trip.html' : 'pages/trip.html';
    } else if (navAction.screen === 'home') {
      targetUrl = isInsidePages ? '../index.html' : 'index.html';
    }

    if (targetUrl) {
        setTimeout(() => {
            close();
            window.location.href = targetUrl;
        }, 1200);
    }
  };

  // Audio-Reactive Canvas Orb Visualizer
  let time = 0;
  const startOrbRenderLoop = () => {
    if (!canvasEl || !ctx) return;

    const render = () => {
      if (!isOpen) return;
      time += 0.016;
      let audioEnergy = 0;

      if (analyser && timeDomainBuffer && !isMuted) {
        analyser.getFloatTimeDomainData(timeDomainBuffer);
        const pitchData = detectPitchFromBuffer(timeDomainBuffer, audioContext ? audioContext.sampleRate : 16000);
        audioEnergy = pitchData.rms * 2.8;

        if (pitchData.pitchHz > 60 && pitchData.pitchHz < 900) {
          currentPitchHz = pitchData.pitchHz;
          smoothedPitchHz += (currentPitchHz - smoothedPitchHz) * 0.09;
          normalizedPitch += ((Math.min(Math.max((smoothedPitchHz - 80) / 400, 0), 1)) - normalizedPitch) * 0.08;

          if (smoothedPitchHz < 145) pitchRegister = 'Deep Bass';
          else if (smoothedPitchHz < 275) pitchRegister = 'Warm Mid';
          else pitchRegister = 'High Register';

          if (pitchBadgeEl) {
            pitchBadgeEl.textContent = `🎵 Pitch: ${Math.round(smoothedPitchHz)} Hz • ${pitchRegister}`;
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
        audioEnergy = 0.05 + 0.02 * Math.sin(time * 1.2);
        if (pitchBadgeEl) pitchBadgeEl.textContent = `🎵 Ready • Tap to Speak`;
      }

      smoothedVolume += (audioEnergy - smoothedVolume) * 0.08;

      const width = canvasEl.width;
      const height = canvasEl.height;
      const centerX = width / 2;
      const centerY = height / 2;
      const baseRadius = 45 + smoothedVolume * 20;

      ctx.clearRect(0, 0, width, height);
      ctx.save();

      // Multi-layer Organic Fluid Silk Rings
      const numLayers = 4;
      for (let layer = numLayers; layer >= 1; layer--) {
        ctx.beginPath();
        const layerRadius = baseRadius * (0.65 + layer * 0.22);
        const points = 64;

        for (let i = 0; i <= points; i++) {
          const angle = (i / points) * Math.PI * 2;
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

        const grad = ctx.createRadialGradient(
          centerX - 8 * Math.sin(time * 0.8),
          centerY - 8 * Math.cos(time * 0.8),
          6,
          centerX,
          centerY,
          layerRadius * 1.25
        );

        // Golden Brass & Temple Jade Hue
        grad.addColorStop(0, `rgba(255, 253, 248, ${0.75 / layer})`);
        grad.addColorStop(0.35, `rgba(185, 154, 91, ${0.48 / layer})`);
        grad.addColorStop(0.75, `rgba(35, 74, 53, ${0.30 / layer})`);
        grad.addColorStop(1, `rgba(23, 53, 37, 0)`);

        ctx.fillStyle = grad;
        ctx.fill();
      }

      // Guiding Star Core
      const starSpikes = 8;
      ctx.fillStyle = 'rgba(255, 253, 248, 0.92)';
      ctx.shadowColor = 'rgba(185, 154, 91, 0.5)';
      ctx.shadowBlur = 8 + smoothedVolume * 8;
      
      ctx.beginPath();
      for (let s = 0; s < starSpikes; s++) {
        const starAngle = (s / starSpikes) * Math.PI * 2 + time * 0.25;
        const outerR = 9 + smoothedVolume * 6;
        const innerR = 3;
        const ox = centerX + Math.cos(starAngle) * outerR;
        const oy = centerY + Math.sin(starAngle) * outerR;
        const ix = centerX + Math.cos(starAngle + Math.PI / starSpikes) * innerR;
        const iy = centerY + Math.sin(starAngle + Math.PI / starSpikes) * innerR;

        if (s === 0) ctx.moveTo(ox, oy);
        else ctx.lineTo(ox, oy);
        ctx.lineTo(ix, iy);
      }
      ctx.closePath();
      ctx.fill();
      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);
  };

  return {
    init,
    open,
    close,
    toggleMicrophone,
    resetConversation,
    handleUserInput
  };
})();

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', DhruvaVoiceOrb.init);

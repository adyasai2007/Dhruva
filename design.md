# DHRUVA — Design System & Visual Direction

## 1. Brand Identity & Product Vision

**DHRUVA** (*"The Guiding Pole Star"*) provides clear, culturally anchored direction for travelers exploring India's heritage, sacred shrines, and timeless traditions.

**Core Tagline:** *DHRUVA — Your Journey, Guided.*

```text
Warm Parchment (Base) + Temple Green (Brand) + Brass Gold (Accent)
               Editorial Typography + Spacious Layouts
          Audio-Reactive Voice Halo + Dark Mode Support
```

---

## 2. Visual Mood & Aesthetic Philosophy

Avoid generic bright-blue corporate booking aesthetics. DHRUVA embodies:

$$\text{Warm} + \text{Cultural} + \text{Editorial} + \text{Premium} + \text{Accessible} + \text{Calm}$$

### Aesthetic Tenets
- **Warm Parchment Grounding:** Surfaces evoke aged paper, temple stone, and hand-woven silks rather than stark digital white.
- **Deep Temple Green:** Evokes sacred groves, sanctum doorways, and quiet confidence.
- **Brass & Gold Accents:** Reminiscent of ceremonial oil lamps (*diyas*) and temple brass work.
- **Accessible Contrast:** High readability prioritizing adults aged 40–65+.

---

## 3. Color Tokens & Theme System

All design tokens are defined in `frontend/css/variables.css`.

### Light Theme (Warm Parchment)

```css
:root {
  /* Surfaces & Canvas */
  --color-bg: #F7F2E8;              /* Warm Parchment ground */
  --color-surface: #FFFDF8;         /* Crisp Warm White Card Ground */
  --color-surface-soft: #F1EBDD;    /* Subtle tinted container background */
  --color-surface-elevated: #FFFFFF;

  /* Brand Colors */
  --color-primary: #234A35;         /* Deep Temple Green */
  --color-primary-dark: #173525;    /* Dark Forest */
  --color-primary-soft: #DDE7DC;    /* Soft Sage Green Tint */

  /* Accent Tones */
  --color-accent: #B99A5B;          /* Burnished Brass Gold */
  --color-accent-soft: #EEE2C8;     /* Soft Gold Champagne */
  --color-accent-hover: #9E8144;

  /* Typography & Text */
  --color-text: #20231F;            /* Deep Charcoal Slate */
  --color-text-secondary: #66675F;  /* Medium Charcoal */
  --color-text-muted: #8A887E;      /* Muted Parchment Grey */

  /* Borders & Dividers */
  --color-border: #DED8C9;
  --color-border-subtle: #ECE6D8;

  /* Functional Status */
  --color-success: #47714D;
  --color-warning: #A97B32;
  --color-error: #A95245;
}
```

### Dark Theme — *Sacred Night* (`.dark-theme`)

```css
:root.dark-theme,
body.dark-theme {
  --color-bg: #101713;              /* Midnight Forest */
  --color-surface: #16211A;         /* Dark Sanctum Green-Black */
  --color-surface-soft: #1D2C23;
  --color-surface-elevated: #24352B;

  --color-primary: #5A9473;         /* Luminous Jade */
  --color-primary-dark: #3F6E54;
  --color-primary-soft: #1C3326;

  --color-accent: #D4B26F;          /* Radiant Gold */
  --color-accent-soft: #38301D;
  --color-accent-hover: #E5C788;

  --color-text: #EDE8DE;            /* Soft Ivory Cream */
  --color-text-secondary: #B0ABA0;  /* Silver Ash */
  --color-text-muted: #7E7C74;

  --color-border: #2B3A30;
  --color-border-subtle: #212D26;
}
```

---

## 4. Typography Scale

- **Display & Editorial Titles:** `Cormorant Garamond`, Georgia, serif — evokes literary heritage, architectural inscriptions, and cultural gravity.
- **UI, Body & Functional Labels:** `Plus Jakarta Sans`, -apple-system, sans-serif — modern, geometric, exceptionally readable.

```css
--font-serif: 'Cormorant Garamond', Georgia, serif;
--font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Typography Scale */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 2rem;      /* 32px */
--text-4xl: 2.5rem;    /* 40px */
--text-display: 3.5rem;/* 56px */
```

---

## 5. Spacing, Radii & Depth

### Spacing Tokens
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
```

### Border Radii
```css
--radius-sm: 8px;
--radius-md: 14px;
--radius-lg: 20px;
--radius-xl: 28px;
--radius-pill: 9999px;
```

### Elevation & Shadows
```css
--shadow-sm: 0 2px 8px rgba(32, 35, 31, 0.04);
--shadow-md: 0 6px 20px rgba(32, 35, 31, 0.07);
--shadow-lg: 0 14px 36px rgba(32, 35, 31, 0.11);
--shadow-glow: 0 0 24px rgba(185, 154, 91, 0.35); /* Brass Gold Halo */
```

---

## 6. Voice Orb & Visual Halo Specification

The **Dhruva Voice Orb** (`frontend/css/voice-orb.css` & `frontend/js/voice-orb.js`) provides an audio-reactive, conversational interface.

```text
       ┌───────────────────────────────┐
       │   Golden Expanding Rings       │
       │   (((   [🎙️ Microphone]   )))   │
       │   Pitch & Volume Responsive    │
       └───────────────────────────────┘
```

### Visual Specifications
1. **Trigger Button (`.voice-orb-btn`):**
   - Floating circular action button (bottom-right: `32px, 32px`).
   - Deep Temple Green ground with Brass Gold border and animated idle pulsing halo.
2. **Audio-Reactive Canvas Halo (`#voiceHaloCanvas`):**
   - Renders multiple concentric golden rings reacting to the user's vocal pitch and volume.
   - Low pitch / calm speech = wide, gentle golden glow.
   - High pitch / animated speech = high-frequency harmonic ripples.
3. **State Modulations:**
   - `idle`: Gentle breathing glow (`--shadow-glow`).
   - `listening`: Golden pulsing radial gradient with audio wave bars.
   - `processing`: Orbital spinning ring in burnished brass.
   - `speaking`: Harmonic pulse synchronized with TTS vocal output.

---

## 7. Component Library Guidelines (`frontend/css/components.css`)

### 1. Destination & Place Cards (`.destination-card`, `.place-card`)
- Rounded corners (`--radius-lg`), warm white surface, subtle border (`--color-border`).
- Aspect-ratio locked hero imagery (`4:3` or `16:9`) with smooth hover zoom (`scale(1.03)`).
- Clear typography hierarchy: Title (serif), location badge, duration pill, and interest tag chips.

### 2. Interactive Step Wizard (`pages/trip.html`)
- Clean 4-step progressive disclosure wizard.
- Large clickable option cards for pacing selection (*Relaxed*, *Comfortable*, *Immersive*).
- Multi-select rounded interest chips with checkmark transitions.

### 3. Cultural Itinerary Timeline (`pages/itinerary.html`)
- Continuous vertical timeline connector with milestone dots.
- Time-badge pill (`08:30 AM`), sanctum visiting guidelines, walking duration, and dress etiquette notes.

### 4. Accessibility Controls
- **Large Text Mode (`.text-scale-large`):** Globally scales base font size by `+20%`.
- **High Contrast Mode (`.high-contrast`):** Intensifies borders to solid `#000000`/`#FFFFFF`, maximizes text contrast to pure `#000` / `#FFF`.

---

## 8. Responsive Breakpoints (`frontend/css/responsive.css`)

```css
/* Mobile Viewports */
@media (max-width: 640px) { ... }

/* Tablets & Small Laptops */
@media (max-width: 992px) { ... }

/* High-Density Desktop */
@media (min-width: 1200px) { ... }
```
- Navigation collapses into an accessible mobile drawer on screens `< 992px`.
- Multi-column grids smoothly collapse to single-column card feeds with touch-friendly tap targets ($\ge 48\text{px}$).

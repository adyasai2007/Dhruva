# DHRUVA --- Design System & Visual Direction

## 1. Primary Visual Reference

The supplied travel-planner screenshot is the **primary visual
reference** for DHRUVA.

It is a reference for visual language, not a template to copy.

DHRUVA should capture the reference's:

-   warm
-   premium
-   editorial
-   calm
-   image-led
-   spacious
-   culturally rich
-   sophisticated but accessible

character while developing its own identity.

------------------------------------------------------------------------

## 2. Brand Identity

### Name

**DHRUVA**

### Brand concept

Dhruva represents a guiding star. The product should therefore feel like
a reliable guide that gives travelers direction through unfamiliar
destinations.

### Tagline

**DHRUVA --- Your Journey, Guided.**

Supporting language may include:

-   Plan with purpose.
-   Discover with context.
-   Travel with direction.
-   Every journey has a direction.

------------------------------------------------------------------------

## 3. Overall Visual Mood

Avoid the generic bright-blue travel-booking aesthetic.

The visual language should communicate:

``` text
Warm + Cultural + Editorial + Premium + Calm + Accessible
```

Avoid:

-   excessive gradients
-   neon colors
-   excessive glassmorphism
-   overly saturated backgrounds
-   cramped dashboards
-   heavy shadows
-   tiny typography
-   constant animation

------------------------------------------------------------------------

## 4. Color System

The core direction is a warm cream/off-white foundation with deep green
accents and dark neutral text.

Recommended starting tokens:

``` css
--color-bg: #F7F2E8;
--color-surface: #FFFDF8;
--color-surface-soft: #F1EBDD;

--color-primary: #234A35;
--color-primary-dark: #173525;
--color-primary-soft: #DDE7DC;

--color-text: #20231F;
--color-text-secondary: #66675F;
--color-text-muted: #8A887E;

--color-border: #DED8C9;

--color-accent: #B99A5B;
--color-accent-soft: #EEE2C8;

--color-success: #47714D;
--color-warning: #A97B32;
--color-error: #A95245;
```

These are starting tokens and can be tuned during implementation.

### Color rules

-   Cream/off-white dominates the interface.
-   Deep green is the main brand/action color.
-   Charcoal is used for important text.
-   Gold/brass is a restrained accent.
-   Accent colors must not compete with photography.
-   Contrast must remain strong enough for comfortable reading.

------------------------------------------------------------------------

## 5. Typography

Typography should feel editorial and premium while remaining highly
readable for the 40--65+ primary audience.

### Direction

Use a highly readable sans-serif for body and interface text.

A restrained serif may be introduced selectively for:

-   major destination titles
-   editorial headings
-   cultural storytelling moments

Do not use decorative typography for functional UI.

### Hierarchy

``` text
Display
Page heading
Section heading
Card heading
Body
Secondary text
Metadata
```

Use comfortable line height and avoid unnecessarily small labels.

------------------------------------------------------------------------

## 6. Layout

DHRUVA is **web-first**.

The initial design should prioritize desktop/web composition while
remaining responsive enough for a future mobile version.

### Desktop

-   centered content container
-   generous margins
-   clear hierarchy
-   multi-column layouts where useful
-   large destination photography
-   comfortable card padding
-   clear navigation

### Responsive principle

Do not create layouts dependent on fixed widths. Components should be
able to collapse naturally into a mobile composition later.

------------------------------------------------------------------------

## 7. Navigation

Primary navigation:

``` text
Home
Plan
Best Time
My Plan
```

Additional actions may include:

-   search
-   profile
-   voice assistance

Navigation should remain visually quiet and should not compete with
destination imagery.

------------------------------------------------------------------------

## 8. Cards

Cards are a major visual structure.

Characteristics:

-   rounded corners
-   warm/white surfaces
-   subtle borders
-   restrained shadows
-   generous padding
-   strong imagery
-   readable titles
-   concise metadata

### Destination card structure

``` text
┌─────────────────────────┐
│                         │
│       Destination       │
│         image           │
│                         │
├─────────────────────────┤
│ Destination name        │
│ Short description       │
│ Category • Time         │
│                         │
│ View / Add              │
└─────────────────────────┘
```

Do not overload cards with information.

------------------------------------------------------------------------

## 9. Photography

Destination photography is central to the product identity.

Images should communicate:

-   place
-   culture
-   architecture
-   landscape
-   atmosphere
-   people/community where appropriate

Prefer large rounded images, natural photography, consistent aspect
ratios, and subtle cropping.

Avoid heavy filters, low-quality imagery, and inconsistent image
proportions.

------------------------------------------------------------------------

## 10. Buttons

Buttons should feel calm and confident.

### Primary

Deep green background with high-contrast light text.

Examples:

``` text
Plan My Trip
Generate My Plan
```

### Secondary

Cream/light surface with dark green text and/or a subtle border.

Examples:

``` text
Explore
View Details
```

### Tertiary

Text or icon actions for low-priority operations.

Avoid multiple dominant CTAs on one screen.

------------------------------------------------------------------------

## 11. Form Controls

Planning inputs should feel conversational rather than bureaucratic.

Examples:

``` text
Where are you going?
When are you traveling?
How much time do you have?
What are you interested in?
```

Controls should use:

-   large interaction targets
-   clear labels
-   rounded surfaces
-   obvious selected states
-   concise helper text

Interest selections should use rounded chips/pills.

------------------------------------------------------------------------

## 12. Interest Chips

Potential interests:

-   Heritage
-   Architecture
-   Food
-   History
-   Spiritual
-   Markets
-   Nature
-   Festivals
-   Local Culture

Selected chips should use DHRUVA green or a soft green selected surface.

------------------------------------------------------------------------

## 13. Itinerary

The itinerary must prioritize clarity.

Suggested visual model:

``` text
DAY 01
Morning
   │
   ├── Place
   │   Description
   │
   ↓
Lunch
   │
   ↓
Afternoon
   │
   ├── Place
   │
   ↓
Evening
```

A timeline structure can be used where it improves comprehension.

Each item should communicate:

-   time
-   location
-   activity
-   duration
-   travel information where useful

------------------------------------------------------------------------

## 14. Best Time

Best Time should feel informative rather than data-heavy.

Use simple visual summaries such as:

-   month/season indicators
-   recommended-time badges
-   seasonal information
-   event highlights
-   opening-hour information

The most important recommendation should be visually obvious.

------------------------------------------------------------------------

## 15. Home

The home screen should immediately communicate what DHRUVA does.

Potential structure:

``` text
Top navigation

Hero
"Where will you go next?"
Supporting statement
Primary planning CTA

Featured destinations

Plan around your interests

Best time highlights

Cultural discovery

My Plan / return-to-trip section

Footer
```

The exact composition can evolve during implementation.

------------------------------------------------------------------------

## 16. Explore

Explore should be image-led and discovery-focused.

Potential elements:

-   search
-   destination categories
-   featured destinations
-   place cards
-   cultural categories
-   filters
-   destination detail entry points

Avoid turning Explore into a dense marketplace grid.

------------------------------------------------------------------------

## 17. Trip Planner

Break complex planning into manageable steps:

``` text
Destination
      ↓
Date
      ↓
Available time
      ↓
Trip duration
      ↓
Interests
      ↓
Generate Plan
```

Use progressive disclosure where possible.

The user should always know:

-   where they are
-   what information is needed
-   what happens next

------------------------------------------------------------------------

## 18. My Plan

My Plan should feel personal and calm.

Potential sections:

-   current trip
-   upcoming trips
-   saved plans
-   itinerary shortcut
-   destination image
-   dates
-   status

------------------------------------------------------------------------

## 19. Voice Feature

Voice assistance is part of the DHRUVA product vision.

A **custom halo interface** will be designed separately.

For the current phase:

-   treat voice as a product capability
-   reserve a suitable interaction point
-   use a simple microphone/voice entry point if required
-   do not implement the final halo
-   do not lock the interface to a specific voice technology

------------------------------------------------------------------------

## 20. Spacing

Use a consistent spacing scale:

``` text
4px
8px
12px
16px
24px
32px
40px
48px
64px
80px
```

Prefer generous spacing over dense layouts.

------------------------------------------------------------------------

## 21. Border Radius

Suggested tokens:

``` css
--radius-sm: 8px;
--radius-md: 14px;
--radius-lg: 20px;
--radius-xl: 28px;
--radius-pill: 999px;
```

Cards and major containers should generally use medium-to-large radii.

------------------------------------------------------------------------

## 22. Shadows

Use subtle shadows only.

The interface should feel elevated without looking like a stack of
floating dashboard cards.

Prefer:

-   thin borders
-   tonal separation
-   restrained depth

over heavy shadows.

------------------------------------------------------------------------

## 23. Iconography

Icons should be:

-   simple
-   consistent
-   recognizable
-   lightweight
-   accessible

Do not mix unrelated icon styles.

------------------------------------------------------------------------

## 24. Animation

Animation should support comprehension.

Good uses:

-   hover feedback
-   button feedback
-   page transitions
-   itinerary expansion
-   selection states
-   loading states

Avoid constant movement and distracting effects.

Suggested transition range:

``` text
150ms–300ms
```

------------------------------------------------------------------------

## 25. Accessibility

Accessibility is a core requirement because the primary audience
includes adults 40--65+.

Prioritize:

-   readable font sizes
-   strong contrast
-   generous click targets
-   clear labels
-   visible focus states
-   understandable icons
-   non-color-only status communication
-   keyboard-friendly navigation
-   responsive layouts

Critical information must never depend only on color.

------------------------------------------------------------------------

## 26. Responsive Strategy

Define breakpoints centrally.

Suggested starting values:

``` css
--breakpoint-mobile: 640px;
--breakpoint-tablet: 768px;
--breakpoint-desktop: 1024px;
--breakpoint-wide: 1280px;
```

These can be tuned during implementation.

------------------------------------------------------------------------

## 27. Quality Bar

DHRUVA should feel:

**intentional, premium, calm, culturally rooted, accessible, and
production-ready.**

It should not feel like:

-   a generic college project
-   a raw Bootstrap template
-   a dense admin dashboard
-   a direct clone of the reference
-   an unstructured AI-generated UI

The reference provides the visual direction. DHRUVA must retain its own
identity.

------------------------------------------------------------------------

## 28. Design Tokens First

Before building individual pages, establish reusable variables for:

-   colors
-   typography
-   spacing
-   radii
-   shadows
-   transitions
-   breakpoints

Every page should consume these tokens rather than inventing unrelated
values.

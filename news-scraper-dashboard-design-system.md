# News Scraper Dashboard Design System

## 1. Product Intent

This design system supports a read-only morning briefing dashboard for a robotics and AI news scraper. The interface should feel fast, credible, and editorial rather than corporate admin software.

The dashboard is optimized for three behaviors:

1. Scan the latest run in under 60 seconds.
2. Understand why each story matters without opening every article.
3. Copy social output and jump into archive history with minimal friction.

## 2. Design Principles

### Signal First
Every surface should help users find the most important information quickly. Density is welcome when hierarchy stays clear.

### Editorial, Not Generic SaaS
The visual language should borrow from modern financial desks and newsroom dashboards: crisp typography, restrained color, deliberate emphasis, and strong data framing.

### Calm Automation
The product is powered by an automated pipeline, but the UI should avoid looking robotic. Status, freshness, and confidence should be visible without becoming noisy.

### Accessibility Is a Product Feature
Keyboard flow, contrast, readable type, and copyable content are core to the experience.

## 3. Brand Direction

### Personality
- Alert
- Precise
- Modern
- Analytical
- Trustworthy

### Visual Tone
- Base palette: ink, slate, stone, cloud
- Accent palette: news cyan for action, signal green for success, ember for warnings
- Surfaces: layered neutrals with subtle tint shifts rather than flat white
- Shape language: medium rounding, sharp internal structure

## 4. Information Architecture

### Primary Sections
1. Morning Brief
2. Top Stories
3. Social Posts
4. Archive

### Global Layout
- Sticky top header with date, run status, and theme toggle
- Left rail on desktop for section jumps and archive shortcuts
- Single-column flow on mobile
- Main content max width: `1360px`

### Reading Order
1. Run health and summary
2. High-priority stories
3. Copy-ready social posts
4. Historical runs

## 5. Design Tokens

### 5.1 Color Tokens

#### Primitive Palette

```json
{
  "color": {
    "primitive": {
      "ink": {
        "50": "#f4f7fb",
        "100": "#e9eef5",
        "200": "#cfd8e4",
        "300": "#aab9cc",
        "400": "#7d90aa",
        "500": "#5f718a",
        "600": "#485971",
        "700": "#334156",
        "800": "#202b3d",
        "900": "#111827",
        "950": "#09111d"
      },
      "cyan": {
        "50": "#ecfeff",
        "100": "#cffafe",
        "200": "#a5f3fc",
        "300": "#67e8f9",
        "400": "#22d3ee",
        "500": "#06b6d4",
        "600": "#0891b2",
        "700": "#0e7490",
        "800": "#155e75",
        "900": "#164e63",
        "950": "#083344"
      },
      "green": {
        "50": "#effef5",
        "100": "#d9fbe7",
        "200": "#b4f4cf",
        "300": "#7ee8ae",
        "400": "#45d488",
        "500": "#21b86a",
        "600": "#179654",
        "700": "#157746",
        "800": "#145e3a",
        "900": "#124d31",
        "950": "#082c1c"
      },
      "amber": {
        "50": "#fff9eb",
        "100": "#ffefc6",
        "200": "#ffdd88",
        "300": "#ffc84a",
        "400": "#ffb020",
        "500": "#f68b12",
        "600": "#d96a0b",
        "700": "#b34b0d",
        "800": "#933a12",
        "900": "#782f12",
        "950": "#451606"
      },
      "red": {
        "50": "#fff1f2",
        "100": "#ffe0e3",
        "200": "#ffc6cc",
        "300": "#ff9ca8",
        "400": "#ff6479",
        "500": "#fb3554",
        "600": "#e11d48",
        "700": "#be123c",
        "800": "#9f1239",
        "900": "#881337",
        "950": "#4c0519"
      },
      "white": "#ffffff",
      "black": "#000000"
    }
  }
}
```

#### Semantic Palette

```json
{
  "color": {
    "semantic": {
      "brand": {
        "primary": "#0891b2",
        "primaryHover": "#0e7490",
        "primaryActive": "#155e75"
      },
      "text": {
        "primary": "#111827",
        "secondary": "#485971",
        "tertiary": "#5f718a",
        "inverse": "#f4f7fb"
      },
      "background": {
        "canvas": "#f4f7fb",
        "surface": "#ffffff",
        "surfaceMuted": "#e9eef5",
        "surfaceStrong": "#202b3d"
      },
      "border": {
        "subtle": "#e9eef5",
        "default": "#cfd8e4",
        "strong": "#aab9cc"
      },
      "feedback": {
        "success": "#179654",
        "warning": "#d96a0b",
        "error": "#e11d48",
        "info": "#0891b2"
      },
      "story": {
        "robotics": "#0e7490",
        "aiResearch": "#334156",
        "aiProduct": "#0891b2",
        "funding": "#179654",
        "policy": "#b34b0d"
      }
    }
  }
}
```

#### Dark Theme Semantic Overrides

```json
{
  "color": {
    "dark": {
      "text": {
        "primary": "#f4f7fb",
        "secondary": "#cfd8e4",
        "tertiary": "#aab9cc"
      },
      "background": {
        "canvas": "#09111d",
        "surface": "#111827",
        "surfaceMuted": "#202b3d",
        "surfaceStrong": "#334156"
      },
      "border": {
        "subtle": "#202b3d",
        "default": "#334156",
        "strong": "#485971"
      }
    }
  }
}
```

### 5.2 Typography Tokens

The system uses an editorial sans paired with a restrained serif accent for rare moments like the daily brief title or archive feature callouts.

```json
{
  "typography": {
    "fontFamily": {
      "sans": "'Manrope', 'Inter', 'Segoe UI', sans-serif",
      "serif": "'Fraunces', 'Georgia', serif",
      "mono": "'IBM Plex Mono', 'Consolas', monospace"
    },
    "fontSize": {
      "xs": "0.75rem",
      "sm": "0.875rem",
      "base": "1rem",
      "lg": "1.125rem",
      "xl": "1.25rem",
      "2xl": "1.5rem",
      "3xl": "1.875rem",
      "4xl": "2.25rem",
      "5xl": "3rem"
    },
    "fontWeight": {
      "regular": 400,
      "medium": 500,
      "semibold": 600,
      "bold": 700
    },
    "lineHeight": {
      "tight": 1.15,
      "snug": 1.3,
      "normal": 1.5,
      "relaxed": 1.65
    },
    "letterSpacing": {
      "tight": "-0.03em",
      "normal": "0",
      "wide": "0.04em"
    }
  }
}
```

### 5.3 Type Roles

- Display: `3xl` to `5xl`, serif optional, used sparingly
- Section heading: `xl` to `2xl`, sans, semibold
- Card title: `lg`, semibold
- Body: `base`, regular
- Metadata: `sm`, medium
- Utility labels: `xs`, medium, wide tracking

### 5.4 Spacing Tokens

Use a 4px base scale.

```json
{
  "spacing": {
    "0": "0",
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "8": "2rem",
    "10": "2.5rem",
    "12": "3rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem"
  }
}
```

### 5.5 Radius Tokens

```json
{
  "borderRadius": {
    "none": "0",
    "sm": "0.25rem",
    "base": "0.5rem",
    "md": "0.75rem",
    "lg": "1rem",
    "xl": "1.25rem",
    "2xl": "1.5rem",
    "pill": "9999px"
  }
}
```

### 5.6 Shadow Tokens

```json
{
  "shadow": {
    "sm": "0 1px 2px rgba(9, 17, 29, 0.06)",
    "base": "0 8px 24px rgba(32, 43, 61, 0.08)",
    "md": "0 18px 40px rgba(17, 24, 39, 0.12)",
    "lg": "0 28px 72px rgba(9, 17, 29, 0.16)"
  }
}
```

### 5.7 Motion Tokens

```json
{
  "motion": {
    "duration": {
      "fast": "120ms",
      "base": "180ms",
      "slow": "280ms"
    },
    "easing": {
      "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
      "exit": "cubic-bezier(0.4, 0, 1, 1)"
    }
  }
}
```

Motion should reinforce scanability. Use fade-and-rise, highlight sweeps, and copy confirmations. Avoid constant pulsing or decorative movement in the story list.

### 5.8 Z-Index Tokens

```json
{
  "zIndex": {
    "base": 0,
    "sticky": 100,
    "dropdown": 200,
    "overlay": 300,
    "toast": 400
  }
}
```

## 6. Theme Model

### Light Theme
- Default for daytime reading
- Bright canvas with cool-neutral surfaces
- Cyan used for action and active navigation

### Dark Theme
- Deep editorial night mode for early-morning use
- Keep contrast strong and reduce pure black
- Preserve category colors, slightly brightened for dark surfaces

### CSS Variable Naming

```css
:root {
  --bg-canvas: #f4f7fb;
  --bg-surface: #ffffff;
  --text-primary: #111827;
  --text-secondary: #485971;
  --border-default: #cfd8e4;
  --brand-primary: #0891b2;
  --status-success: #179654;
}

[data-theme="dark"] {
  --bg-canvas: #09111d;
  --bg-surface: #111827;
  --text-primary: #f4f7fb;
  --text-secondary: #cfd8e4;
  --border-default: #334156;
  --brand-primary: #22d3ee;
  --status-success: #45d488;
}
```

## 7. Layout System

### Breakpoints

```json
{
  "breakpoints": {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1440px"
  }
}
```

### Grid
- Mobile: 4 columns
- Tablet: 8 columns
- Desktop: 12 columns
- Story cards: 1 column on mobile, 2 columns on large desktop
- Social posts: full-width stack on mobile, 2-column stagger on desktop

### Containers
- App shell max width: `1360px`
- Reading content max width inside cards: `72ch`
- Rail width: `248px`

## 8. Component Architecture

### 8.1 Atoms

#### Button
Variants:
- `primary`
- `secondary`
- `ghost`
- `quiet`
- `destructive`

Sizes:
- `sm`
- `md`
- `lg`

Key uses:
- Refresh latest run
- Copy social post
- Open source article
- Jump to archive day

#### Icon Button
Used for theme toggle, copy, external link, and compact row actions. Minimum hit target: `44x44px`.

#### Badge
Variants:
- `status-success`
- `status-warning`
- `status-error`
- `status-info`
- `category-robotics`
- `category-ai-research`
- `category-ai-product`
- `category-funding`
- `category-policy`

#### Text Link
Supports inline links and "read source" patterns. External links should expose an icon and accessible label.

#### Divider
Used to split metric groups, card subsections, and archive rows.

#### Timestamp
Small metadata atom for `published_at`, `completed_at`, and relative freshness.

### 8.2 Molecules

#### Run Status Pill
Composition:
- Status dot
- Label
- Optional helper text

States:
- `scheduled`
- `running`
- `partial`
- `completed`
- `failed`

#### KPI Stat
Composition:
- Eyebrow label
- Value
- Delta or helper note

Primary stats:
- Selected stories
- Discovery candidates
- Social posts generated
- Run completion time

#### Section Header
Composition:
- Title
- Supporting description
- Optional action

#### Story Meta Row
Composition:
- Source
- Published time
- Category badge
- Rank index

#### Copy Block
Composition:
- Body text
- Character count
- Copy button
- Copied state confirmation

#### Archive Row
Composition:
- Date
- Run status
- Story count
- Open action

### 8.3 Organisms

#### App Header
Contains:
- Product title
- Current date/run label
- Theme toggle
- Refresh action

#### Navigation Rail
Contains:
- Section anchors
- Latest run shortcut
- Archive shortcuts

Desktop behavior:
- Sticky within viewport

Mobile behavior:
- Collapses into horizontal section tabs

#### Morning Brief Panel
Contains:
- Run date
- Intro summary
- KPI stat strip
- Pipeline status block

This panel is the hero. It should feel like the cover of a morning briefing, not a dashboard banner.

#### Story Card
Contains:
- Rank
- Headline
- Story meta row
- Short summary
- Why it matters
- Source CTA

Variants:
- `featured` for the top-ranked story
- `standard` for remaining stories

#### Social Posts Panel
Contains:
- Section header
- Copy blocks
- Optional helper text about platform length

#### Archive List
Contains:
- Search or filter later, not required for MVP
- Reverse-chronological run list
- Status and count visibility

#### Empty State
Used when no run exists yet or a section has no content. Tone should be matter-of-fact, not playful.

#### Error Banner
Used for partial or failed runs. Must explain what still succeeded.

### 8.4 Templates

#### Latest Run Template
- Header
- Morning Brief hero
- Featured story
- Story grid
- Social posts
- Archive rail/list

#### Archive Day Template
- Compact header with back-to-latest action
- Prior run metadata
- Story list
- Social posts

### 8.5 Pages

#### Latest Dashboard Page
Default landing experience. Prioritize the most recent completed or partially completed run.

#### Archived Run Page
Same structure with slightly reduced hero emphasis.

## 9. Detailed Component Specs

### Story Card

#### Content Order
1. Rank
2. Headline
3. Source and timestamp
4. Category
5. Summary short
6. Why it matters
7. Outbound link

#### Visual Rules
- Headline gets strongest emphasis
- Summary max 3 lines before natural wrap expansion
- Why-it-matters block should feel distinct through tint or rule
- External CTA stays visually quiet until hover/focus

### Social Copy Block

#### Behavior
- One-click copy
- Inline success confirmation
- Preserve line breaks exactly
- Show character count in monospace

#### States
- `default`
- `hover`
- `copied`
- `error`

### Archive Row

#### Behavior
- Entire row clickable
- Hover should reveal stronger date emphasis
- Failed or partial runs should remain visible, not filtered out

## 10. Content Guidelines

### Headlines
- Preserve original article headlines
- Truncate carefully only in compact lists

### Summaries
- Aim for one dense sentence or two short lines
- Avoid hype language
- Prefer specific nouns over vague abstractions

### Why It Matters
- Start with impact, not recap
- Good: "Signals renewed enterprise appetite for warehouse autonomy."
- Avoid: "This is important because it matters to the industry."

### Labels
- Use plain language
- Prefer `Top Stories` over `Curated Intelligence Objects`

## 11. Accessibility Requirements

### Contrast
- Body text: minimum `4.5:1`
- Large headings and badges: minimum `3:1`
- Copy buttons, chips, and focus rings must remain visible in both themes

### Keyboard
- Full page usable without a mouse
- Sticky rail anchors reachable in logical order
- Copy buttons expose visible focus state
- Theme toggle and external links use semantic buttons/anchors

### Screen Readers
- Use semantic landmarks: `header`, `nav`, `main`, `section`, `article`, `aside`
- Story cards should be `article` elements
- External links announce destination intent
- Copy success feedback should use polite live region messaging

### Focus
- Focus ring token: `2px solid var(--brand-primary)` with `2px` offset
- Do not remove browser outline without replacement

### Mobile Touch
- Minimum hit target `44x44px`
- Keep row spacing generous enough for thumb scanning

## 12. State Design

### Run Status Mapping
- `scheduled`: neutral slate treatment
- `running`: info cyan with subtle animated indicator
- `completed`: green
- `partial`: amber
- `failed`: red

### Loading
- Use skeleton blocks for hero stats and story cards
- Avoid spinner-only layouts for primary content areas

### Partial Failure UX
- If social generation fails but stories exist, render the brief and show a scoped warning in the social section
- If some article extractions fail, do not elevate the failure above the completed content

## 13. Implementation Guidance

### Recommended Token Export Shape
- `tokens/color.json`
- `tokens/typography.json`
- `tokens/spacing.json`
- `tokens/elevation.json`
- `tokens/motion.json`

### Recommended Component Folders

```text
components/
  atoms/
    Button
    Badge
    IconButton
    Timestamp
  molecules/
    RunStatusPill
    KPIStat
    StoryMetaRow
    CopyBlock
    ArchiveRow
  organisms/
    AppHeader
    NavigationRail
    MorningBriefPanel
    StoryCard
    SocialPostsPanel
    ArchiveList
  templates/
    LatestRunTemplate
    ArchiveRunTemplate
```

### Naming Guidance
- Prefer semantic names over visual ones
- Good: `status-partial-bg`
- Avoid: `yellow-card-bg`

## 14. MVP Delivery Priority

### P0
- Color, type, spacing, radius, shadow tokens
- App shell
- Morning Brief panel
- Story card
- Social copy block
- Archive row/list
- Light and dark themes
- Accessibility baseline

### P1
- Richer category treatments
- Sticky rail enhancements
- Skeleton system
- More expressive empty/error states

### P2
- Search/filter in archive
- Advanced motion polish
- Editorial spotlight layouts for major stories

## 15. Acceptance Checklist

- Tokens cover light and dark themes
- Latest run can be scanned in under one minute
- Story cards support 5 to 8 items cleanly across breakpoints
- Social posts are copyable with clear success feedback
- Archive rows communicate status and date at a glance
- Keyboard-only navigation works end to end
- Contrast meets WCAG 2.1 AA
- Partial runs still feel intentional, not broken

## 16. Summary

This system should feel like a daily intelligence terminal for robotics and AI, not a CRUD dashboard. The combination of crisp hierarchy, cool editorial surfaces, disciplined accent color, and strong status signaling should make the product trustworthy at 9:00 AM and still pleasant when someone checks yesterday's run at night.

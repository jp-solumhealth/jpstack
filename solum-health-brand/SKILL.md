# Solum Health Brand Guidelines Skill

Use this skill automatically when creating any content, web pages, HTML documents, landing pages, one-pagers, or marketing materials for Solum Health. This ensures all output is on-brand.

---

## Logo

- **Primary logo (dark on light):** Use on light backgrounds (#F2F2F9 or white)
  - Logo URL: `https://cdn.prod.website-files.com/66ccf770fcc17846279d79cd/6748cf9b5bac5ff27b9e6bff_solumnewlogo.avif`
  - Fallback PNG: `https://bookface-images.s3.us-west-2.amazonaws.com/logos/00f1dcaca9dbe257d62b042870af7f0cb1833251.png`
- **Reversed logo (white on dark):** Use on Navy (#011C40) backgrounds
- **Icon-only mark:** The globe/S mark can be used standalone as a favicon or avatar
- The wordmark reads **SolumHealth** (one word, capital S and capital H, no space)

---

## Color Palette

### Primary Colors
| Name            | Hex       | Usage                                                    |
|-----------------|-----------|----------------------------------------------------------|
| Navy            | `#011C40` | Primary brand color. Headers, footers, dark backgrounds, text on light surfaces |
| Light Gray      | `#F2F2F9` | Page backgrounds, light sections, card backgrounds       |
| Solum Blue      | `#468AF7` | Primary accent. Buttons, links, interactive elements, CTA highlights |

### Secondary / Accent Colors
| Name            | Hex       | Usage                                                    |
|-----------------|-----------|----------------------------------------------------------|
| Light Blue      | `#CCEAE5` | Subtle background tints, secondary cards                 |
| Lavender        | `#E5DFF4` | Light accent backgrounds, tags, badges                   |
| Teal            | `#70D3C6` | Success states, positive indicators, secondary accent    |
| Purple          | `#A16CF4` | Tertiary accent, highlights, callouts                    |
| Dark Teal       | `#146055` | Dark accent for contrast, secondary text on light bg     |
| Deep Purple     | `#462E7D` | Dark accent alternative, premium/emphasis elements       |

### Neutral / UI Colors
| Name            | Hex       | Usage                                                    |
|-----------------|-----------|----------------------------------------------------------|
| Near White      | `#F9F9F9` | Subtle background variation                              |
| Dark Text       | `#111111` | Body text, maximum contrast                              |

### Gradients
- Blue-to-purple gradient: `linear-gradient(135deg, #468AF7, #A16CF4)` — for hero sections, featured CTAs
- Teal-to-blue gradient: `linear-gradient(135deg, #70D3C6, #468AF7)` — for secondary highlights
- Full spectrum: `linear-gradient(90deg, #A16CF4, #E5DFF4, #70D3C6, #011C40, #468AF7)` — for decorative borders or thin accent lines

---

## Typography

- **Font family:** `'DM Sans', sans-serif`
- **Google Fonts import:** `@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&display=swap');`
- **Weights used:**
  - `400` (Regular) — Body text, descriptions
  - `500` (Medium) — Subheadings, labels, navigation
  - `700` (Bold) — Headlines, emphasis, buttons, session titles
- **Italic variants** available for all weights — use for quotes, annotations, secondary info

### Type Scale (recommended)
| Element         | Size   | Weight | Letter-spacing |
|-----------------|--------|--------|----------------|
| H1 / Hero       | 32–40px | 700    | -0.5px         |
| H2 / Section    | 22–28px | 700    | -0.3px         |
| H3 / Card Title | 14–18px | 700    | 0              |
| Body            | 14–16px | 400    | 0              |
| Caption / Label | 10–12px | 500    | 0.3–0.5px      |
| Small / Fine    | 8–10px  | 400    | 0.2px          |

---

## Design Principles

1. **Navy-first hierarchy:** Use Navy (#011C40) for primary headers, footers, and time/date blocks. It anchors every layout.
2. **Blue for action:** Solum Blue (#468AF7) is reserved for links, buttons, CTAs, and interactive highlights.
3. **Light backgrounds:** Default page background is #F2F2F9 or #F9F9F9. Use white (#FFFFFF) for cards.
4. **Accent sparingly:** Teal (#70D3C6) and Purple (#A16CF4) are supporting colors — use for tags, badges, callout borders, and decorative accents. Never as primary background for large areas.
5. **Generous whitespace:** Solum's brand feels clean and professional. Maintain at least 16px padding inside cards, 24px+ between sections.
6. **Border radius:** Use `8px` for cards and containers, `20px` for pills/badges, `6px` for small elements.
7. **Shadows (minimal):** `box-shadow: 0 1px 3px rgba(1, 28, 64, 0.08)` for subtle card elevation.

---

## CSS Starter Template

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400;1,500;1,700&display=swap');

:root {
  /* Primary */
  --solum-navy: #011C40;
  --solum-light-gray: #F2F2F9;
  --solum-blue: #468AF7;

  /* Secondary */
  --solum-light-blue: #CCEAE5;
  --solum-lavender: #E5DFF4;
  --solum-teal: #70D3C6;
  --solum-purple: #A16CF4;
  --solum-dark-teal: #146055;
  --solum-deep-purple: #462E7D;

  /* Neutrals */
  --solum-near-white: #F9F9F9;
  --solum-dark-text: #111111;
  --solum-white: #FFFFFF;
}

body {
  font-family: 'DM Sans', sans-serif;
  color: var(--solum-dark-text);
  background: var(--solum-light-gray);
  line-height: 1.5;
}
```

---

## Contact Information (for Solum Health materials)

- **JP Montoya**, CEO, Solum Health
- Email: jp@getsolum.com
- Phone: (628) 276-2659
- Website: getsolum.com

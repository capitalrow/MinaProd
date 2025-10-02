# Mina Design System - Crown+ Quality

## Overview

The Mina Design System is a comprehensive set of design tokens, components, and guidelines that ensure visual consistency and premium quality across the entire application.

**Philosophy**: Ultra-premium, enterprise-grade aesthetics with deep glass morphism, sophisticated gradients, and delightful micro-interactions.

## Design Tokens

All design tokens are defined in `/static/css/mina-tokens.css` as CSS custom properties (variables).

### Color Palette

#### Primary Colors (Brand Blue)
- `--color-primary-400` through `--color-primary-900`
- Use for: Primary actions, links, brand elements
- Example: Buttons, navigation highlights

#### Secondary Colors (Purple)
- `--color-secondary-400` through `--color-secondary-900`
- Use for: Secondary actions, accents, highlights
- Example: Secondary buttons, badges

#### Accent Colors (Green)
- `--color-accent-400` through `--color-accent-900`
- Use for: Success states, positive actions
- Example: Success messages, completed tasks

#### Semantic Colors
- **Error**: `--color-error-*` (Red)
- **Warning**: `--color-warning-*` (Orange/Yellow)
- **Neutral**: `--color-neutral-*` (Grayscale)

#### Background Colors
```css
--bg-primary: #0a0e17;      /* Main background */
--bg-secondary: #0f1419;    /* Secondary surfaces */
--bg-tertiary: #161b22;     /* Elevated surfaces */
--bg-glass: rgba(255, 255, 255, 0.05);  /* Glass morphism */
```

#### Text Colors
```css
--text-primary: #f0f6fc;    /* Main text */
--text-secondary: #8b949e;  /* Secondary text */
--text-tertiary: #6e7681;   /* Muted text */
```

### Spacing Scale

Based on 4px base unit:
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

**Usage Guidelines**:
- Padding: Use `--space-4` to `--space-8`
- Margins: Use `--space-4` to `--space-12`
- Gaps: Use `--space-2` to `--space-6`

### Typography

#### Font Families
```css
--font-sans: 'Inter', sans-serif;  /* Primary */
--font-mono: 'Fira Code', monospace;  /* Code */
```

#### Type Scale
```css
--text-xs: 0.75rem;    /* 12px - Labels, captions */
--text-sm: 0.875rem;   /* 14px - Small text */
--text-base: 1rem;     /* 16px - Body text */
--text-lg: 1.125rem;   /* 18px - Large text */
--text-xl: 1.25rem;    /* 20px - Headings */
--text-2xl: 1.5rem;    /* 24px - Section headings */
--text-4xl: 2rem;      /* 32px - Page headings */
--text-6xl: 3rem;      /* 48px - Hero headings */
```

#### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### Line Heights
```css
--leading-tight: 1.25;    /* Headings */
--leading-normal: 1.5;    /* Body text */
--leading-relaxed: 1.625; /* Long-form content */
```

### Shadows & Depth

#### Standard Shadows
```css
--shadow-sm: Small elevation
--shadow-md: Medium elevation
--shadow-lg: Large elevation
--shadow-xl: Extra large elevation
```

#### Glass Morphism Shadows
```css
--shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
--shadow-glass-hover: Hover state with more depth
```

#### Glow Effects
```css
--glow-primary: Primary brand glow
--glow-secondary: Secondary glow
--glow-accent: Success/accent glow
```

### Border Radius

```css
--radius-base: 0.25rem;   /* 4px - Small elements */
--radius-lg: 0.5rem;      /* 8px - Cards, buttons */
--radius-xl: 0.75rem;     /* 12px - Large cards */
--radius-2xl: 1rem;       /* 16px - Modals */
--radius-full: 9999px;    /* Circular */
```

### Transitions & Animations

#### Durations
```css
--duration-150: 150ms;  /* Fast interactions */
--duration-200: 200ms;  /* Standard */
--duration-300: 300ms;  /* Slow/smooth */
```

#### Easing Functions
```css
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);  /* Standard */
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);  /* Playful */
--ease-smooth: cubic-bezier(0.25, 0.46, 0.45, 0.94);  /* Smooth */
```

#### Common Transitions
```css
--transition-fast: all 150ms ease-out;
--transition-base: all 200ms ease-in-out;
--transition-colors: Smooth color transitions;
```

### Glass Morphism

#### Background Blur
```css
--glass-blur: blur(20px);      /* Standard */
--glass-blur-lg: blur(30px);   /* Strong */
```

#### Glass Backgrounds
```css
--glass-bg: rgba(255, 255, 255, 0.05);
--glass-bg-hover: rgba(255, 255, 255, 0.08);
--glass-bg-active: rgba(255, 255, 255, 0.12);
```

#### Glass Borders
```css
--glass-border: 1px solid rgba(255, 255, 255, 0.1);
```

## Component Patterns

### Glass Card
```html
<div class="glass-card">
  <!-- Content -->
</div>
```

```css
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: var(--glass-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-glass);
  transition: var(--transition-base);
}

.glass-card:hover {
  background: var(--glass-bg-hover);
  box-shadow: var(--shadow-glass-hover);
}
```

### Button Variants

#### Primary Button
```css
.btn-primary {
  background: var(--gradient-primary);
  color: var(--text-primary);
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-lg);
  font-weight: var(--font-semibold);
  transition: var(--transition-base);
  box-shadow: var(--shadow-md);
}

.btn-primary:hover {
  box-shadow: var(--shadow-lg), var(--glow-primary);
  transform: translateY(-1px);
}
```

#### Glass Button
```css
.btn-glass {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: var(--glass-border);
  /* ... */
}
```

## Responsive Design

### Breakpoints
```css
/* Mobile: < 640px */
/* Tablet: 640px - 1024px */
/* Desktop: > 1024px */
```

### Spacing Adjustments
- Mobile: `--base-padding: 16px`
- Tablet: `--base-padding: 24px`
- Desktop: `--base-padding: 32px`

## Accessibility

### Color Contrast
- All text meets WCAG 2.1 AA contrast requirements
- Primary text: 7:1 minimum contrast
- Secondary text: 4.5:1 minimum contrast

### Focus States
- Visible focus ring: `2px solid var(--border-focus)`
- Focus offset: `2px`

### Interactive Elements
- Minimum touch target: 44x44px
- Clear hover states
- Keyboard accessible

## Usage Guidelines

### DO
✅ Use design tokens for all values
✅ Follow the spacing scale
✅ Use semantic color names
✅ Apply glass morphism consistently
✅ Include smooth transitions

### DON'T
❌ Hardcode color values
❌ Use arbitrary spacing
❌ Mix design systems
❌ Forget hover/focus states
❌ Ignore accessibility

## Implementation

### In HTML/Templates
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/mina-tokens.css') }}">
```

### In CSS Files
```css
@import url('mina-tokens.css');

.my-component {
  background: var(--bg-glass);
  padding: var(--space-6);
  border-radius: var(--radius-xl);
}
```

### In JavaScript
```javascript
const primaryColor = getComputedStyle(document.documentElement)
  .getPropertyValue('--color-primary-500');
```

## Examples

See the Live Recording Studio page for the benchmark Crown+ quality that all pages should match.

## Updates

When adding new tokens:
1. Add to `mina-tokens.css`
2. Document here with examples
3. Update component library
4. Test across all pages

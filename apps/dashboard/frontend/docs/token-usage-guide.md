# Design Token Usage Guide

This pack uses Material Design 3-style token categories.

## Color

Use semantic color roles, not raw color names.

Good:

```css
color: var(--md-sys-color-on-surface);
background: var(--md-sys-color-surface-container);
border-color: var(--md-sys-color-outline-variant);
```

Avoid:

```css
color: #222;
background: #f7f7f7;
border-color: #ddd;
```

## Typography

Use type roles: display, headline, title, body, and label. Map these to product needs rather than arbitrary font sizes.

## Shape

Use shape tokens consistently: small for chips/buttons, medium for cards/forms, large for dialogs/sheets, extra large for large panels.

## Elevation

Use elevation sparingly. Avoid putting shadows on every card.

## Motion

Use motion to explain state changes, not to decorate. Respect reduced motion when implementing animations.

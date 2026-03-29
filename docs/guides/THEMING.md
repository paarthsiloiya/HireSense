# Theming Guidelines

This application uses Tailwind CSS v4 configured via the browser CDN. Rather than a traditional build process with `tailwind.config.js`, all design tokens and colors are centralized inside the `@theme` CSS directive in `base.html`.

This structure makes it exceptionally easy to re-brand the application entirely from a single location without altering individual HTML elements or running a build tool.

## 1. Naming Conventions

Always use our defined semantic tokens instead of hardcoded default Tailwind colors (e.g., `green-500`, `gray-100`).

### Brand Colors:
*   **`primary`**: The core theme tint (e.g., `text-primary-800`, `bg-primary-950`). Replaces the `green` palette.
  *   Available weights: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950.

### Structural Colors:
*   **`bg-surface`**: Defines the background of foreground elements like cards, panels, dropdowns, and auth boxes (Replaces `bg-white`).
*   **`bg-background`**: Translates to the app's overall backdrop root color (Replaces `bg-gray-100` / `bg-gray-50`).

### Text Colors:
*   **`text-text-main`**: For the vast majority of strong headings and paragraphs (Replaces `text-gray-900`, `text-black`).
*   **`text-text-muted`**: Used for secondary paragraphs, subtitles, and less prominent UI elements (Replaces `text-gray-500`, `text-gray-600`, `text-gray-700`).
*   **`text-text-light`**: Softest text option for hints, placeholders, and subtle borders (Replaces `text-gray-300`, `text-gray-400`).
*   **`text-text-inverse`**: Contrasting colors meant to be placed over primary/surface backgrounds (Replaces `text-white`).

### Border Colors:
*   **`border-border-main`**: A standard color for component outlines, dividers, line breaks, and input fields. Supports `border-`, `divide-`, and `ring-` utilities.

### State / Alerts:
*   **`danger`**: Errors, deletions, invalid states (replaces `red`).
*   **`success`**: Confirmations, achievements, positive paths (replaces `green` alerts).
*   **`info`**: General notifications (replaces `blue` alerts).

---

## 2. Using the Theme in New Components

When building a new component or page, strictly stick to standard semantic tokens:

**Bad (Don't do this):**
```html
<div class="bg-white border rounded-md border-gray-300 shadow">
  <h2 class="text-black text-xl">Confirm the action</h2>
  <button class="bg-green-600 text-white hover:bg-green-700 p-2">Submit</button>
</div>
```

**Good (Do this):**
```html
<div class="bg-surface border rounded-md border-border-main shadow">
  <h2 class="text-text-main text-xl">Confirm the action</h2>
  <button class="bg-primary-600 text-text-inverse hover:bg-primary-700 p-2">Submit</button>
</div>
```

---

## 3. How to Extend or Modify the Theme

To tweak the entire site's color scheme, you only edit **`app/templates/base.html`** in the `<style type="text/tailwindcss">` block. 

### Changing the Primary Color Palette
For instance, to rebrand the app from Green to **Indigo**, just update the mappings in `base.html` like so:

```css
@theme {
  --color-primary-50: var(--color-indigo-50);
  --color-primary-100: var(--color-indigo-100);
  --color-primary-200: var(--color-indigo-200);
  ...
  --color-primary-950: var(--color-indigo-950);
}
```
Reloading the page will instantly tint the sidebar, active states, buttons, auth headers, and overlays globally to indigo without requiring any HTML modifications.

### Dark Mode (Future)
If introducing a dark mode later, you could adjust the `background`, `surface`, `text-main`, and `border-main` toggles in response to dark media queries within that same `@theme` block.
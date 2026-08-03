# learning

Reference notes published as a static site.

**→ [nikolay-e.github.io/learning](https://nikolay-e.github.io/learning/)**

## Contents

| Page                       | What it is                                                                                                                                                                       |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`index.html`](index.html) | Принципы программной инженерии: от SOLID до AI-эры — 62 principles grouped by axis, with examples in Java 21+, Rust, Go and Python 3.12+, plus a table of conflicts between them |

## Local preview

```bash
python3 -m http.server 8000
open http://localhost:8000
```

No build step, no dependencies. `assets/highlight.min.js` is vendored so the page works offline
and renders identically without a CDN.

## Site features

- Language switcher — pick Java / Rust / Go / Python and every code block on the page follows
- `/` focuses the filter box; typing narrows the page to matching principles
- Light and dark themes, persisted per browser
- Print stylesheet expands every language pane

## Deployment

GitHub Pages serves `main` from the repository root. Pushing to `main` publishes.

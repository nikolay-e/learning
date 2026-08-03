# learning

Reference notes published as a static site.

**→ [nikolay-e.github.io/learning](https://nikolay-e.github.io/learning/)**

## Contents

| Page                       | What it is                                                                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`index.html`](index.html) | Принципы программной инженерии: от SOLID до AI-эры — 87 principles grouped by axis, with examples in Java, Rust, Go and Python 3.12+, plus a table of conflicts between them |

## Local preview

```bash
python3 -m http.server 8000
open http://localhost:8000
```

No build step, no dependencies. `assets/highlight.min.js` (plus the `protobuf` grammar, which the
common bundle omits) is vendored so the page works offline and renders identically without a CDN.
highlight.js 11 ships no HCL/Terraform grammar and no third-party one is on cdnjs, so the one
Terraform block is marked `plaintext` rather than pulling an extra dependency or faking the
language.

## Site features

- Language switcher — pick Java / Rust / Go / Python and every code block on the page follows
- `/` focuses the filter box; typing narrows the page to matching principles. Each principle
  carries `data-keywords` with English synonyms, so Russian-titled entries are findable by
  their canonical English name ("robustness principle", "thundering herd", "false sharing")
- Light and dark themes, persisted per browser
- Print stylesheet expands every language pane

Principle numbers are stable identifiers: new entries are appended to the numbering and
placed in the topical section, so numbering inside a section is not contiguous.

## Deployment

GitHub Pages serves `main` from the repository root. Pushing to `main` publishes.

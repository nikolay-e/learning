# learning

Reference notes published as a static site.

**→ [nikolay-e.github.io/learning](https://nikolay-e.github.io/learning/)**

## Contents

| Page                       | What it is                                                                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`index.html`](index.html) | Принципы программной инженерии: от SOLID до AI-эры — 88 principles grouped by axis, with examples in Java, Rust, Go and Python 3.12+, plus a table of conflicts between them |

Every entry is classified: `theorem`, `empirical-law`, `heuristic`, `pattern`, `practice` or
`editorial`, with a confidence level next to it. Amdahl's law and "choose boring technology"
are not the same kind of claim and the page does not pretend otherwise. Where the wording is
stronger than the evidence, the card carries an explicit scope note.

All code is **fragments** — real syntax, not self-contained programs; they lean on types and
imports off-screen. Each figure says so, and CI checks what can be checked statically.

## Local preview

```bash
python3 -m http.server 8000
open http://localhost:8000
```

The published page has **no runtime dependencies**: no CDN, no fonts, no network calls. The
one inline script sits in `<head>` and applies the saved theme before the stylesheet loads, so
light-theme readers do not get a dark flash on every visit.
`assets/highlight.min.js` and the `protobuf` grammar are vendored, with versions and SHA-256
hashes recorded in [`THIRD_PARTY.md`](THIRD_PARTY.md). There is a build step, but it runs
before commit, not in the browser — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

highlight.js 11 ships no HCL/Terraform grammar and no third-party build of one is on cdnjs,
so the single Terraform example is marked `plaintext` rather than adding a dependency or
mislabelling the language.

## Site features

- Language switcher — pick Java / Rust / Go / Python and every code block follows. Where a
  figure has no example in the selected language it says so instead of silently showing a
  different one
- `/` focuses the filter; typing narrows the page and updates `?q=` so a filtered view is
  linkable. Each principle carries English synonyms, so Russian-titled entries are findable
  by their canonical English name ("robustness principle", "thundering herd", "false sharing")
- Light and dark themes, persisted per browser; both pass axe at WCAG 2.1 AA
- Keyboard: `/` for filter, arrow keys across language tabs, skip link, focus-visible rings
- Print stylesheet forces a light palette and expands every language pane
- Copy button labels each language when copying a multi-language figure

Principle numbers are stable identifiers: new entries are appended to the numbering and placed
in the topical section, so numbering inside a section is not contiguous. Nothing is renumbered,
and a number freed by a deleted entry is retired rather than handed to a new one — `#pNN` links
keep meaning what they meant.

## Working on it

`index.html` is generated from `content/` — do not edit it by hand.

```bash
python3 scripts/build.py     # content/ -> index.html
npm install                  # build and QA tooling only
npm run check                # validate + html-validate + prettier + Playwright + axe
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) covers the source layout and what is required of a new
entry. [`SECURITY.md`](SECURITY.md) covers reporting.

## Deployment

GitHub Pages serves `main` from the repository root. Pushing to `main` publishes.

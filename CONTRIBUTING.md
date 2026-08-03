# Contributing

## The generated file

`index.html` is **generated**. Do not edit it by hand — edit `content/` and rebuild:

```bash
python3 scripts/build.py
```

CI fails if the committed `index.html` differs from what `content/` produces.

## Layout

```
content/principles/NNN-slug.yaml   one principle: title, nav label, keywords, ordered blocks
content/metadata.yaml              kind / confidence / example_status / caveat / sources
content/sections.yaml              section order, numerals, which principles they hold
content/conflicts.yaml             conflict table; refs generate the back-links on cards
content/site.yaml                  hero, meta, badge vocabularies
templates/page.html                page shell
scripts/build.py                   content -> index.html
scripts/validate.py                integrity checks (also run in CI and pre-commit)
tests/                             Playwright behaviour + axe accessibility
```

## Adding a principle

1. Create `content/principles/0NN-slug.yaml`. `id` is the next free number — numbers are
   stable identifiers and are never reused or renumbered, so a new principle keeps its number
   even though it lands in an older section.
2. Add its `id` to the right section in `content/sections.yaml`.
3. Add an entry to `content/metadata.yaml`. `kind`, `confidence` and `example_status` are
   mandatory; `validate.py` rejects the build without them.
4. Rebuild and run the checks.

## Classification is not decoration

Every claim carries a type. A theorem, an empirical observation and a personal editorial
position are presented differently on purpose — if you cannot honestly pick `kind` and
`confidence`, the entry is not ready. When the wording is stronger than the evidence, put the
limitation in `caveat` rather than softening the headline into mush.

Add `sources` only for links you have actually opened. An invented citation is worse than
none, and `validate.py` cannot tell the difference.

## Examples

Every snippet is a fragment: real syntax, not a self-contained program. Mark what it is with
`example_status` (`fragment`, `config`, `pseudocode`, `none`). Python fragments are parsed by
`validate.py`, so they must at least be syntactically valid.

Do not claim an API exists without checking the version. If behaviour depends on a runtime
version, say so in `versions` — it renders on the card.

## Checks

```bash
npm install                # build/test tooling only, never shipped to the browser
npm run check              # validate + html-validate + prettier + Playwright + axe
```

## Tool conflicts, resolved deliberately

- `index.html` is excluded from Prettier. It is generated; letting a formatter and a generator
  rewrite the same file in turn would make "the build is current" unverifiable. Correctness of
  the generated markup is covered by `html-validate` instead.
- `doctype-style` is disabled in `.htmlvalidate.json`: Prettier emits `<!doctype html>`,
  html-validate prefers uppercase, both are valid HTML5. Prettier owns `templates/page.html`,
  so Prettier wins.
- `content/` is excluded from Prettier: it reformats the YAML into flow mappings, and these
  files exist to be read by humans.

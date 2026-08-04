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

`title` is inserted as raw HTML, so it can carry markup — and must carry its own entities
(`&gt;` for `>`). `nav_label`, `keywords` and table cells are escaped by the generator; do not
pre-escape those or the entity shows up literally.

## Removing a principle

Numbers are permanent identifiers and `validate.py` also requires the numbering to be gapless,
which is only possible if a deleted number stays accounted for. Delete the principle file, its
`metadata.yaml` entry, its `sections.yaml` slot and any `conflicts.yaml` refs — then add the
number to the top-level `retired:` list in `content/sections.yaml`. The number is burned: it
counts towards continuity and `validate.py` rejects any attempt to hand it to a new card.
`#pNN` links live in other people's bookmarks, so silently reassigning a number rewrites what
they saved.

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
pip install -r scripts/requirements.txt   # PyYAML, for build.py and validate.py
npm install                               # build/test tooling, never shipped to the browser
npm run check                             # validate + html-validate + prettier + Playwright + axe
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
- `templates/page.html` carries one inline `<script>` in `<head>`, and it is the only script
  allowed to be inline. It applies the stored or system theme before the stylesheet loads;
  doing it from `assets/app.js` at the end of `<body>` flashes the dark palette on every load
  for light-theme readers. "No runtime dependencies" is about the network, not about this.
- `scripts/validate.py` builds into a temporary file and compares. It never writes
  `index.html`: a check that repairs what it checks turns a failing pre-commit into a silently
  mutated working tree.

# QA playbook — learning

Project-specific only. Generic patterns live in `~/.claude/qa-refs/`.

## What this project is

Static reference site, no backend, no database, no auth, no users. Published by GitHub Pages
from `main` at the repository root. `index.html` is **generated** from `content/` by
`scripts/build.py` — never hand-edited, and CI fails if the committed file has drifted.

## Applicability matrix

| Checklist item           | Applies | Why                                                        |
| ------------------------ | ------- | ---------------------------------------------------------- |
| Forge / CI               | yes     | GitHub, Actions (`ci.yml` per push, `links.yml` weekly)    |
| CD / ArgoCD / K8s / pods | no      | GitHub Pages, no cluster                                   |
| Backend smoke / DB       | no      | no backend                                                 |
| Client-error telemetry   | no      | no ingest endpoint; a beacon would need a backend          |
| Browser QA               | yes     | the page is the whole product                              |
| Tests                    | yes     | `npm test` — Playwright + axe, desktop and mobile projects |
| Autoqa pipeline / pin    | no      | no autoqa job (see "Standing in for autoqa")               |
| SonarCloud               | no      | no Sonar project, no `sonar-project.properties`            |
| Bug intake               | partial | GitHub issues — the only channel (see "Bug channels")      |
| Test accounts            | no      | nothing to log into                                        |

## Forge

GitHub (`github.com/nikolay-e/learning`) — this repo is the documented exception to the
workspace's Forgejo-first rule, because GitHub Pages is the hosting. Use `gh`.

## Deploy check

```bash
gh api repos/nikolay-e/learning/pages/builds/latest --jq '{status,commit,error:.error.message}'
```

`commit` must equal `git rev-parse HEAD`. Two workflows fire per push — `ci` (ours) and
`pages-build-deployment` (GitHub's). A green `ci` does not mean the page shipped; check both.

That API endpoint lags: it kept reporting the previous SHA for minutes after
`pages-build-deployment` had already finished green for the new one. The workflow run is the
authoritative signal, the endpoint is not — cross-check with

```bash
gh run list --workflow=pages-build-deployment --limit 3 \
  --json status,conclusion,headSha --jq '.[]|"\(.status) \(.conclusion) \(.headSha[0:7])"'
```

and confirm against the served bytes (`curl` the page and grep for something the new commit
introduced) before concluding the deploy is stuck.

The mirror-image trap costs more time: **a browser that already visited the page serves the
old HTML from its own cache.** Re-navigating to the same URL after a deploy shows pre-deploy
content while `curl` shows the new bytes — that contradiction is the browser, not Pages. Add a
throwaway query (`?cachebust=<sha>`) for every post-deploy browser check; `curl` is the
tiebreaker.

## Production verification

Anything asserting against production must use the **trailing slash**:
`https://nikolay-e.github.io/learning/`. Playwright's `page.goto("/")` resolves against the
origin, so a `baseURL` without the trailing slash silently loads `nikolay-e.github.io/` — a
different page that returns 200 and zero principles. This looks exactly like a catastrophic
regression and is not one. The repo's own config points at localhost, where `/` is correct.

Production smoke worth re-running by hand: 89 articles, every `pre code` carrying `hljs`,
zero axe violations at WCAG 2.1 AA in light + dark + mobile, zero console errors, and no dark
flash on load with the light theme stored (the theme script lives in `<head>` for that reason).

## Content checks that are not in the test suite

`scripts/validate.py` covers structure. What is automated elsewhere, and what still needs a
human:

- **External source links.** Links in `content/metadata.yaml` under `sources` are fetched
  weekly by `.github/workflows/links.yml` (lychee, cron + `workflow_dispatch`), which opens
  an issue instead of failing an unrelated PR. Rot is caught; a citation that resolves but
  never said what the card claims is not — that still needs a human opening the page.
- **Vendored bundle integrity** is no longer manual: `validate.py` re-hashes every
  `assets/*.min.js` against the SHA-256 table in `THIRD_PARTY.md` and fails on a mismatch in
  either direction. A bundle swapped without `scripts/vendor-highlight.sh` no longer ships.
- **Whether a claim is still true.** API surfaces move (Flink `Time`→`Duration`, Java preview
  APIs, Go stdlib). `versions` on a card is a promise about a specific runtime; when a
  release moves, that card is stale even though every check is green. `validate.py` narrows
  the manual pass to a list: it warns (does not fail) for every card carrying `versions`
  whose `last_reviewed` is older than 180 days. Re-read those, then bump the date.

  The 180-day warning is a floor, not the check — a preview API can move twice inside it.
  Web-search each `versions` card against the **current** release rather than trusting the
  page or training memory: this is how p26 was caught shipping `anySuccessfulResultOrThrow()`,
  renamed to `anySuccessfulOrThrow()` when JDK 26 re-previewed structured concurrency under
  JEP 525. Preview APIs (`--enable-preview`) are the highest-risk group: they are re-previewed
  yearly, and each round is free to rename things. Set a per-card `last_reviewed` on the cards
  actually re-verified rather than leaning on the global default.

## Standing in for autoqa

`sync-autoqa-pin.sh --repo .` reports "no autoqa pin, skip" — there is no post-deploy autoqa
job here and no sensor. What the missing pipeline would have covered, and who covers it instead:

- **Crawler / broken links / JS errors / a11y** — the Playwright + axe suite covers the built
  bytes, and CI proves the deployed file equals them. Each pass additionally fetch the served
  page and check every `href`/`src` it contains resolves (27 external + 4 assets today), and
  run axe against **production** in the four combinations the suite covers only locally —
  desktop/mobile × light/dark. A throwaway script under the repo root is the cheapest way:
  `@playwright/test` and `@axe-core/playwright` resolve only from there, not from a scratch
  directory. Delete it before committing. `github.com` answering `429` in a sequential link
  sweep is the QA traffic being rate-limited, not link rot — re-check that one URL alone.
- **Source-link rot on demand** — `links.yml` only runs weekly, so a pass that adds citations
  is not covered by it. `gh workflow run links.yml` after pushing; it checks Markdown too, so
  it also catches a README link the same pass broke.
- **Schemathesis** — nothing to test: no API, no OpenAPI document.
- **ZAP** — deliberately **not** run. An active scan of `nikolay-e.github.io` is a scan of
  GitHub's infrastructure, not of this app; there is no backend, form, cookie or auth here for
  it to find anything in. Skipping is the decision, not an oversight.

## Known-good states that look like problems

- `1 skipped` in the Playwright output is the mobile-menu test skipping itself in the desktop
  project. It runs in the mobile project. Not a disabled test.
- Prettier and html-validate disagree about DOCTYPE case; `doctype-style` is deliberately off.
  `index.html` and `content/` are deliberately outside Prettier. Reasons in `CONTRIBUTING.md`
  under "Tool conflicts, resolved deliberately" — do not "fix" these by re-enabling them.
- `assets/*.min.js` are vendored third-party bundles. Hashes in `THIRD_PARTY.md`; update only
  via `scripts/vendor-highlight.sh`.

## Bug channels

GitHub issues, and nothing else. Re-verified from code each pass, not from memory: no beacon or
`fetch`/`sendBeacon` in `assets/app.js` or the template, no form, no `mailto:`, no backend, no
database, no bot. `links.yml` files into the same GitHub issues channel — an open issue titled
about broken links is that workflow reporting, not a human. If a channel is ever added, list it
here.

## diffctx omits files the repo un-ignores

`SECURITY.md` is hidden by the global `~/.config/git/ignore` (it reserves that filename for
`/review-security` output) and un-ignored here by `!SECURITY.md` in `.gitignore`. `diffctx
--diff` treats a `git check-ignore -v` record as "ignored" and so drops any file matched by a
negation pattern — filed as [diffctx#193](https://github.com/nikolay-e/diffctx/issues/193).

Until that ships: cross-check the diff-context file list against `git diff --name-only <range>`
and read anything missing by hand. The full map (`diffctx .`) is unaffected — only `--diff`.

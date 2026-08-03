# QA playbook — learning

Project-specific only. Generic patterns live in `~/.claude/qa-refs/`.

## What this project is

Static reference site, no backend, no database, no auth, no users. Published by GitHub Pages
from `main` at the repository root. `index.html` is **generated** from `content/` by
`scripts/build.py` — never hand-edited, and CI fails if the committed file has drifted.

## Applicability matrix

| Checklist item           | Applies | Why                                                         |
| ------------------------ | ------- | ----------------------------------------------------------- |
| Forge / CI               | yes     | GitHub, Actions (`.github/workflows/ci.yml`) — not Forgejo  |
| CD / ArgoCD / K8s / pods | no      | GitHub Pages, no cluster                                    |
| Backend smoke / DB       | no      | no backend                                                  |
| Client-error telemetry   | no      | no ingest endpoint; a beacon would need a backend           |
| Browser QA               | yes     | the page is the whole product                               |
| Tests                    | yes     | `npm test` — Playwright + axe, desktop and mobile projects  |
| Autoqa pipeline / pin    | no      | no autoqa job; the Playwright + axe suite is the equivalent |
| SonarCloud               | no      | no Sonar project, no `sonar-project.properties`             |
| Bug intake               | partial | GitHub issues only — the single channel that exists         |
| Test accounts            | no      | nothing to log into                                         |

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

## Production verification

Anything asserting against production must use the **trailing slash**:
`https://nikolay-e.github.io/learning/`. Playwright's `page.goto("/")` resolves against the
origin, so a `baseURL` without the trailing slash silently loads `nikolay-e.github.io/` — a
different page that returns 200 and zero principles. This looks exactly like a catastrophic
regression and is not one. The repo's own config points at localhost, where `/` is correct.

Production smoke worth re-running by hand: 87 articles, every `pre code` carrying `hljs`,
zero axe violations at WCAG 2.1 AA in light + dark + mobile, zero console errors.

## Content checks that are not in the test suite

`scripts/validate.py` covers structure. Two things it cannot check, so check them by hand:

- **External source links.** ~12 links in `content/metadata.yaml` under `sources`. Nothing
  in CI fetches them; curl the list each pass. An invented or rotted citation is worse than
  no citation, and the validator cannot tell the difference.
- **Whether a claim is still true.** API surfaces move (Flink `Time`→`Duration`, Java preview
  APIs, Go stdlib). `versions` on a card is a promise about a specific runtime; when a
  release moves, that card is stale even though every check is green.

## Known-good states that look like problems

- `1 skipped` in the Playwright output is the mobile-menu test skipping itself in the desktop
  project. It runs in the mobile project. Not a disabled test.
- Prettier and html-validate disagree about DOCTYPE case; `doctype-style` is deliberately off.
  `index.html` and `content/` are deliberately outside Prettier. Reasons in `CONTRIBUTING.md`
  under "Tool conflicts, resolved deliberately" — do not "fix" these by re-enabling them.
- `assets/*.min.js` are vendored third-party bundles. Hashes in `THIRD_PARTY.md`; update only
  via `scripts/vendor-highlight.sh`.

## Bug channels

GitHub issues, and nothing else — there is no in-app queue, no bot, no telemetry. If a channel
is ever added, list it here.

# Security

This repository publishes a static page. It has no backend, no forms, no cookies, and no
runtime network calls — every asset is served from the same origin.

## Reporting

Open a private security advisory on GitHub, or email the address on the profile of
[@nikolay-e](https://github.com/nikolay-e). Please do not open a public issue for anything
that looks exploitable.

## What is in scope

- Malicious content reaching the published page (supply chain of the vendored
  `assets/*.min.js`, or a compromised build).
- Anything that would make the page execute third-party code.

## What is out of scope

- Technical inaccuracies in the reference material — those are ordinary issues, not
  security reports.
- Links to external documentation.

## Dependency hygiene

`assets/highlight.min.js` and `assets/hljs-protobuf.min.js` are vendored with recorded
SHA-256 hashes in [`THIRD_PARTY.md`](THIRD_PARTY.md); `scripts/vendor-highlight.sh` is the
only supported way to update them and rewrites those hashes. Build and test dependencies are
pinned through `package-lock.json` and are never shipped to the browser.

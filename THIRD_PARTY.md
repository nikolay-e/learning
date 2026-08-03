# Third-party assets

Vendored into `assets/` so the page has no runtime network dependencies.

| File                          | Project                                                                     | Version | License      | SHA-256                                                            |
| ----------------------------- | --------------------------------------------------------------------------- | ------- | ------------ | ------------------------------------------------------------------ |
| `assets/highlight.min.js`     | [highlight.js](https://github.com/highlightjs/highlight.js) (common bundle) | 11.10.0 | BSD-3-Clause | `471ef9ae90c407af440fcdc48edfeeb562106b3267bd12d99071c162fb52ed32` |
| `assets/hljs-protobuf.min.js` | highlight.js — `protobuf` grammar                                           | 11.10.0 | BSD-3-Clause | `22faafea7ddd968f9f4fd73791400c36a3e1a24005c86903dd7f6479cb144206` |

Both were fetched from `cdnjs.cloudflare.com/ajax/libs/highlight.js/11.10.0/`.

## Updating

```bash
scripts/vendor-highlight.sh 11.11.0   # downloads, verifies, rewrites this table
```

highlight.js 11 ships no HCL/Terraform grammar and no third-party build of one is on cdnjs,
so the single Terraform example is marked `plaintext` rather than adding a dependency or
mislabelling the language.

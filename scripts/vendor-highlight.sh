#!/usr/bin/env bash
# Обновляет вендоренный highlight.js и переписывает таблицу в THIRD_PARTY.md.
# Использование: scripts/vendor-highlight.sh 11.11.0
set -euo pipefail

version="${1:?укажите версию, например 11.11.0}"
root="$(cd "$(dirname "$0")/.." && pwd)"
base="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${version}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -sfL -o "$tmp/highlight.min.js" "$base/highlight.min.js"
curl -sfL -o "$tmp/protobuf.min.js" "$base/languages/protobuf.min.js"

for lang in java rust go python sql yaml kotlin bash markdown ini json; do
  if ! grep -q "grmr_$lang" "$tmp/highlight.min.js"; then
    echo "в бандле $version нет грамматики $lang — обновление отменено" >&2
    exit 1
  fi
done

mv "$tmp/highlight.min.js" "$root/assets/highlight.min.js"
mv "$tmp/protobuf.min.js" "$root/assets/hljs-protobuf.min.js"

sha_main="$(shasum -a 256 "$root/assets/highlight.min.js" | cut -d' ' -f1)"
sha_proto="$(shasum -a 256 "$root/assets/hljs-protobuf.min.js" | cut -d' ' -f1)"

python3 - "$root/THIRD_PARTY.md" "$version" "$sha_main" "$sha_proto" <<'PY'
import re, sys
path, version, sha_main, sha_proto = sys.argv[1:5]
with open(path, encoding="utf-8") as fh:
    text = fh.read()
text = re.sub(r"(\(common bundle\) \| )[\d.]+( \| BSD-3-Clause \| `)[0-9a-f]{64}",
              rf"\g<1>{version}\g<2>{sha_main}", text)
text = re.sub(r"(`protobuf` grammar \| )[\d.]+( \| BSD-3-Clause \| `)[0-9a-f]{64}",
              rf"\g<1>{version}\g<2>{sha_proto}", text)
text = re.sub(r"highlight\.js/[\d.]+/`", f"highlight.js/{version}/`", text)
with open(path, "w", encoding="utf-8") as fh:
    fh.write(text)
PY

echo "highlight.js обновлён до $version — проверьте страницу и закоммитьте"

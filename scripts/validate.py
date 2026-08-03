"""Проверки целостности источника и собранной страницы. Возвращает 1 при любой ошибке."""

import ast
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(name):
    return yaml.safe_load((CONTENT / name).read_text(encoding="utf-8"))


site = load("site.yaml")
meta = load("metadata.yaml")
sections = load("sections.yaml")["sections"]
conflicts = load("conflicts.yaml")["conflicts"]

principles = {}
for path in sorted((CONTENT / "principles").glob("*.yaml")):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data["id"] in principles:
        fail(f"дублирующийся id принципа: {data['id']} ({path.name})")
    principles[data["id"]] = (path, data)

ids = sorted(principles)
expected = list(range(1, len(ids) + 1))
if ids != expected:
    fail(
        f"нумерация принципов не сплошная: пропуски {sorted(set(expected) - set(ids))}"
    )

# --- метаданные -------------------------------------------------------------

for pid, (path, data) in principles.items():
    m = meta["principles"].get(pid)
    if not m:
        fail(f"p{pid}: нет метаданных в metadata.yaml")
        continue
    for field, table in (
        ("kind", "kinds"),
        ("confidence", "confidences"),
        ("example_status", "example_statuses"),
    ):
        if field not in m:
            fail(f"p{pid}: не задано поле {field}")
        elif m[field] not in site[table]:
            fail(f"p{pid}: неизвестное значение {field}={m[field]}")
    has_code = any(b["type"] == "code" for b in data["blocks"])
    if has_code and m.get("example_status") == "none":
        fail(f"p{pid}: example_status=none, но в карточке есть код")
    if not has_code and m.get("example_status") != "none":
        fail(f"p{pid}: кода нет, а example_status={m.get('example_status')}")
    for src in m.get("sources", []):
        if not src.get("url", "").startswith("https://"):
            fail(f"p{pid}: источник без https-ссылки: {src}")

for pid in meta["principles"]:
    if pid not in principles:
        fail(f"metadata.yaml описывает несуществующий принцип {pid}")

# --- разделы ----------------------------------------------------------------

seen = []
for sec in sections:
    for pid in sec["principles"]:
        if pid not in principles:
            fail(f"раздел {sec['id']} ссылается на несуществующий принцип {pid}")
        seen.append(pid)
dupes = {p for p in seen if seen.count(p) > 1}
if dupes:
    fail(f"принципы в нескольких разделах: {sorted(dupes)}")
orphans = set(principles) - set(seen)
if orphans:
    fail(f"принципы вне разделов: {sorted(orphans)}")

numerals = [s["numeral"] for s in sections]
if len(set(numerals)) != len(numerals):
    fail(f"дублирующиеся номера разделов: {numerals}")

# --- конфликты --------------------------------------------------------------

for row in conflicts:
    for pid in row["refs"]:
        if pid not in principles:
            fail(f"конфликт «{row['left']}» ссылается на несуществующий принцип {pid}")
    if not row["refs"]:
        warn(f"конфликт «{row['left']}» ни на что не ссылается")

# --- сборка актуальна -------------------------------------------------------

built = ROOT / "index.html"
before = built.read_text(encoding="utf-8") if built.exists() else ""
subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "build.py")],
    check=True,
    capture_output=True,
)
after = built.read_text(encoding="utf-8")
if before != after:
    fail(
        "index.html не соответствует content/ — запустите scripts/build.py и закоммитьте результат"
    )

# --- собранная страница -----------------------------------------------------

page = after
anchors = set(re.findall(r'\sid="([^"]+)"', page))
for href in set(re.findall(r'href="#([^"]+)"', page)):
    if href not in anchors:
        fail(f"битая внутренняя ссылка: #{href}")

all_ids = re.findall(r'\sid="([^"]+)"', page)
dup_ids = {i for i in all_ids if all_ids.count(i) > 1}
if dup_ids:
    fail(f"дублирующиеся id в HTML: {sorted(dup_ids)}")

for tag in re.findall(r"<button\b[^>]*>", page):
    if 'type="' not in tag:
        fail(f"button без type: {tag[:70]}")

nav_count = len(re.findall(r'<li data-for="p\d+"', page))
if nav_count != len(principles):
    fail(f"в оглавлении {nav_count} пунктов против {len(principles)} принципов")

count = len(principles)
readme = (ROOT / "README.md").read_text(encoding="utf-8")
if f"{count} principles" not in readme:
    fail(f"README не упоминает «{count} principles»")
if f"{count} принципов" not in page:
    fail(f"страница не упоминает «{count} принципов»")

# --- код --------------------------------------------------------------------

checked = 0
for pid, (path, data) in principles.items():
    status = meta["principles"].get(pid, {}).get("example_status")
    for block in data["blocks"]:
        if block["type"] != "code":
            continue
        for pane in block["panes"]:
            code = pane["code"]
            if not code.strip():
                fail(f"p{pid}: пустая панель кода")
            if "\t" in code:
                warn(f"p{pid}: табы в примере ({pane['highlight']})")
            if pane["highlight"] == "python" and status != "pseudocode":
                checked += 1
                try:
                    ast.parse(code)
                except SyntaxError as exc:
                    fail(
                        f"p{pid}: Python-фрагмент не разбирается — {exc.msg} "
                        f"(строка {exc.lineno})"
                    )

print(
    f"принципов: {len(principles)}  разделов: {len(sections)}  "
    f"конфликтов: {len(conflicts)}  python-фрагментов проверено: {checked}"
)
for w in warnings:
    print(f"  warn: {w}")
for e in errors:
    print(f"  FAIL: {e}")
sys.exit(1 if errors else 0)

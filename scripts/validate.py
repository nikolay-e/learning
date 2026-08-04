"""Проверки целостности источника и собранной страницы. Возвращает 1 при любой ошибке."""

import ast
import datetime
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
STALE_AFTER_DAYS = 180

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


class DuplicateKey(Exception):
    pass


class StrictLoader(yaml.SafeLoader):
    pass


def _mapping_without_duplicates(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DuplicateKey(f"«{key}», строка {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_without_duplicates
)


def read(path):
    text = path.read_text(encoding="utf-8")
    try:
        return yaml.load(text, Loader=StrictLoader)
    except DuplicateKey as exc:
        # PyYAML молча берёт последнее значение — так теряется целая карточка
        fail(f"{path.name}: дублирующийся ключ {exc}")
        return yaml.safe_load(text)


def load(name):
    return read(CONTENT / name)


site = load("site.yaml")
meta = load("metadata.yaml")
sections_doc = load("sections.yaml")
sections = sections_doc["sections"]
retired = sections_doc.get("retired") or []
conflicts = load("conflicts.yaml")["conflicts"]

principles = {}
for path in sorted((CONTENT / "principles").glob("*.yaml")):
    data = read(path)
    if data["id"] in principles:
        fail(f"дублирующийся id принципа: {data['id']} ({path.name})")
    principles[data["id"]] = (path, data)

ids = sorted(principles)

# Номер — вечный идентификатор: удалённый принцип уходит в sections.yaml:retired,
# и его номер больше никому не достаётся. Сплошность проверяется по объединению,
# иначе «номера не переиспользуются» и «нумерация без дыр» несовместимы.
bad_retired = [pid for pid in retired if not isinstance(pid, int)]
if bad_retired:
    # без этого sorted() по смеси int и str падает трейсбеком вместо сообщения
    fail(f"retired содержит не номера: {bad_retired}")
    retired = [pid for pid in retired if isinstance(pid, int)]
if len(set(retired)) != len(retired):
    fail(f"дубли в retired: {retired}")
reused = sorted(set(retired) & set(ids))
if reused:
    fail(f"номера из retired переиспользованы: {reused}")
allocated = sorted(set(ids) | set(retired))
expected = list(range(1, len(allocated) + 1))
if allocated != expected:
    fail(
        "нумерация принципов не сплошная: пропуски "
        f"{sorted(set(expected) - set(allocated))} "
        "(удалённый номер должен быть в sections.yaml:retired)"
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
        why = " (номер в retired)" if pid in retired else ""
        fail(f"metadata.yaml описывает несуществующий принцип {pid}{why}")

# --- свежесть версионных утверждений ---------------------------------------

today = datetime.date.today()
default_reviewed = meta.get("defaults", {}).get("last_reviewed")
for pid in sorted(principles):
    m = meta["principles"].get(pid) or {}
    if not m.get("versions"):
        continue
    stamp = m.get("last_reviewed") or default_reviewed
    if not stamp:
        warn(f"p{pid}: есть versions, но нет last_reviewed — свежесть непроверяема")
        continue
    try:
        reviewed = datetime.date.fromisoformat(str(stamp))
    except ValueError:
        fail(f"p{pid}: last_reviewed={stamp!r} — не дата в формате ГГГГ-ММ-ДД")
        continue
    age = (today - reviewed).days
    if age > STALE_AFTER_DAYS:
        warn(
            f"p{pid}: утверждение о версиях не пересматривали {age} дней "
            f"(с {reviewed}) — перепроверьте и обновите last_reviewed"
        )

# --- разделы ----------------------------------------------------------------

seen = []
for sec in sections:
    for pid in sec["principles"]:
        if pid not in principles:
            why = " (номер в retired)" if pid in retired else ""
            fail(f"раздел {sec['id']} ссылается на несуществующий принцип {pid}{why}")
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
            why = " (номер в retired)" if pid in retired else ""
            fail(
                f"конфликт «{row['left']}» ссылается на несуществующий принцип {pid}{why}"
            )
    if not row["refs"]:
        warn(f"конфликт «{row['left']}» ни на что не ссылается")

# --- сборка актуальна -------------------------------------------------------

# Проверка не имеет права чинить то, что проверяет: сборка идёт во временный
# файл, иначе упавший pre-commit молча оставляет рабочее дерево «исправленным».
committed = ROOT / "index.html"
with tempfile.TemporaryDirectory() as tmp:
    fresh = pathlib.Path(tmp) / "index.html"
    build = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build.py"), "--out", str(fresh)],
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        fail(f"build.py упал (код {build.returncode}):\n{build.stderr.strip()}")
        page = committed.read_text(encoding="utf-8") if committed.exists() else ""
    else:
        page = fresh.read_text(encoding="utf-8")
        if not committed.exists():
            fail("index.html не собран — запустите scripts/build.py")
        elif committed.read_text(encoding="utf-8") != page:
            fail(
                "index.html не соответствует content/ — запустите scripts/build.py "
                "и закоммитьте результат"
            )

# --- собранная страница -----------------------------------------------------

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

# --- вендоренные бандлы -----------------------------------------------------

# Хеши в THIRD_PARTY.md — обещание, что в assets/ лежит ровно то, что скачал
# vendor-highlight.sh. Без сверки это обещание никто не проверяет, а подмена
# бандла — единственный способ выполнить чужой код на этой странице.
third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
recorded = dict(re.findall(r"`(assets/[^`]+\.js)`.*?`([0-9a-f]{64})`", third_party))
vendored = sorted(p.name for p in (ROOT / "assets").glob("*.min.js"))
for name in vendored:
    path = ROOT / "assets" / name
    key = f"assets/{name}"
    if key not in recorded:
        fail(f"{key} не описан в THIRD_PARTY.md")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != recorded[key]:
        fail(
            f"{key}: SHA-256 не совпадает с THIRD_PARTY.md "
            f"(в файле {actual[:16]}…, записан {recorded[key][:16]}…) — "
            "обновляйте только через scripts/vendor-highlight.sh"
        )
for key in recorded:
    if not (ROOT / key).is_file():
        fail(f"THIRD_PARTY.md описывает отсутствующий {key}")

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

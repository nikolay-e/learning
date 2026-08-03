"""One-shot migration: index.html -> content/*.yaml. Kept for provenance; build.py is the
forward path."""

import pathlib
import re

import yaml
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOUP = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "lxml")

TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def slugify(text):
    text = text.lower()
    out = "".join(TRANSLIT.get(ch, ch) for ch in text)
    out = re.sub(r"[^a-z0-9]+", "-", out)
    return re.sub(r"-{2,}", "-", out).strip("-")[:48]


def inner(tag):
    return "".join(str(c) for c in tag.contents).strip()


def parse_figure(fig):
    if fig.has_attr("data-multi"):
        tabs = {b["data-lang"]: b.get_text(strip=True) for b in fig.select(".langtab")}
        panes = []
        for pane in fig.select(".codepane"):
            flag = pane.select_one(".paneflag")
            code = pane.select_one("pre code")
            lang = pane["data-lang"]
            panes.append(
                {
                    "lang": lang,
                    "tab": tabs.get(lang, lang),
                    "label": (
                        flag.get_text(strip=True) if flag else tabs.get(lang, lang)
                    ),
                    "highlight": code.get("class", ["language-plaintext"])[
                        0
                    ].removeprefix("language-"),
                    "code": code.get_text(),
                }
            )
        return {"panes": panes}

    label = fig.select_one(".langlabel")
    code = fig.select_one("pre code")
    return {
        "panes": [
            {
                "lang": None,
                "tab": None,
                "label": label.get_text(strip=True) if label else "",
                "highlight": code.get("class", ["language-plaintext"])[0].removeprefix(
                    "language-"
                ),
                "code": code.get_text(),
            }
        ]
    }


def parse_table(wrap):
    table = wrap.find("table")
    head = [th.get_text(strip=True) for th in table.select("thead th")]
    rows = []
    for tr in table.select("tbody tr"):
        rows.append([
            {"html": inner(td), "class": " ".join(td.get("class") or [])}
            for td in tr.find_all("td")
        ])
    return {"type": "table", "head": head, "rows": rows}


def parse_blocks(container, skip_head=True):
    blocks = []
    for child in container.find_all(
        ["p", "figure", "div", "ul", "ol"], recursive=False
    ):
        classes = child.get("class") or []
        if skip_head and "p-head" in classes:
            continue
        if child.name == "figure":
            blocks.append({"type": "code", **parse_figure(child)})
        elif "tablewrap" in classes:
            blocks.append(parse_table(child))
        elif child.name == "p":
            kind = (
                "lede" if "lede" in classes else "note" if "note" in classes else "text"
            )
            blocks.append({"type": kind, "html": inner(child)})
        elif child.name in ("ul", "ol"):
            blocks.append({"type": "list", "html": inner(child)})
    return blocks


nav_labels = {}
for li in SOUP.select(".rail-group li"):
    link = li.find("a")
    num = link.select_one(".rail-num")
    text = link.get_text(" ", strip=True)
    if num:
        text = text[len(num.get_text(strip=True)) :].strip()
    nav_labels[li["data-for"]] = text

sections = []
principles = []

for sec in SOUP.select("section.section"):
    head = sec.select_one(".section-head")
    entry = {
        "id": sec["id"],
        "numeral": head.select_one(".numeral").get_text(strip=True),
        "title": head.find("h2").get_text(strip=True),
        "always": sec.get("data-always") == "1",
        "intro": [],
        "principles": [],
    }
    for node in sec.find_all(["p", "h3", "div"], recursive=False):
        classes = node.get("class") or []
        if "section-head" in classes:
            continue
        if node.name == "h3" and "subhead" in classes:
            nxt = node.find_next("article", class_="principle")
            entry["intro"].append({
                "type": "subhead",
                "text": node.get_text(strip=True),
                "before": nxt["id"] if nxt else None,
            })
        elif node.name == "p":
            kind = ("closing" if "closing" in classes
                    else "note" if "note" in classes else "text")
            entry["intro"].append({"type": kind, "html": inner(node)})
        elif "tablewrap" in classes:
            entry["intro"].append(parse_table(node))

    for art in sec.select("article.principle"):
        num = int(art["id"][1:])
        title = art.select_one(".p-head h3").get_text(strip=True)
        principles.append(
            {
                "id": num,
                "slug": slugify(title),
                "title": title,
                "nav_label": nav_labels.get(art["id"], title),
                "section": sec["id"],
                "keywords": art.get("data-keywords", ""),
                "blocks": parse_blocks(art),
            }
        )
        entry["principles"].append(num)
    sections.append(entry)

# the closing callout lives outside the table section body
closing = SOUP.select_one(".closing")

out_sec = ROOT / "content"
out_sec.mkdir(exist_ok=True)
(out_sec / "sections.yaml").write_text(
    yaml.safe_dump(
        {"sections": sections, "closing": inner(closing) if closing else ""},
        allow_unicode=True,
        sort_keys=False,
        width=100,
    ),
    encoding="utf-8",
)

pdir = out_sec / "principles"
pdir.mkdir(exist_ok=True)
for p in principles:
    (pdir / f"{p['id']:03d}-{p['slug']}.yaml").write_text(
        yaml.safe_dump(p, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )

print(f"sections: {len(sections)}  principles: {len(principles)}")
print(
    "code blocks:",
    sum(
        len(b["panes"]) for p in principles for b in p["blocks"] if b["type"] == "code"
    ),
)

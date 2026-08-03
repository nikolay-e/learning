"""content/*.yaml -> index.html. Единственный способ менять страницу: правишь YAML, гоняешь build."""

import html
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"


def load(name):
    return yaml.safe_load((CONTENT / name).read_text(encoding="utf-8"))


def esc(text):
    return html.escape(text, quote=True)


def load_principles():
    items = []
    for path in sorted((CONTENT / "principles").glob("*.yaml")):
        items.append(yaml.safe_load(path.read_text(encoding="utf-8")))
    return {p["id"]: p for p in items}


def figure_html(block, fig_id, status_label, status_hint):
    panes = block["panes"]
    multi = len(panes) > 1 or panes[0].get("lang")
    available = [p["lang"] for p in panes if p.get("lang")]
    out = []

    attrs = " data-multi" if multi else ""
    if available:
        attrs += f' data-available="{esc(",".join(available))}"'
    out.append(f'<figure class="code"{attrs}>')

    out.append(
        '<figcaption class="sr-only">' f"Пример кода ({esc(status_label)})</figcaption>"
    )

    if multi:
        out.append('<div class="langbar">')
        # role=tablist обязан содержать только tab-элементы, поэтому
        # статус и кнопка копирования живут снаружи этого контейнера
        out.append('<div class="langtabs" role="tablist" aria-label="Язык примера">')
        for pane in panes:
            lang = pane["lang"]
            out.append(
                f'<button type="button" class="langtab" role="tab" id="{fig_id}-tab-{lang}" '
                f'data-lang="{esc(lang)}" aria-selected="false" tabindex="-1" '
                f'aria-controls="{fig_id}-pane-{lang}">{esc(pane["tab"] or lang)}</button>'
            )
    else:
        out.append('<div class="langbar">')
        out.append(f'<span class="langlabel">{esc(panes[0]["label"])}</span>')

    if multi:
        out.append("</div>")
    out.append('<span class="grow"></span>')
    out.append(
        f'<span class="status" title="{esc(status_hint)}">{esc(status_label)}</span>'
    )
    out.append('<button type="button" class="copy">копировать</button>')
    out.append("</div>")

    out.append('<p class="fallback-note" hidden></p>')

    for pane in panes:
        code = f'<pre tabindex="0"><code class="language-{esc(pane["highlight"])}">{esc(pane["code"])}</code></pre>'
        if multi:
            lang = pane["lang"]
            out.append(
                f'<div class="codepane" role="tabpanel" id="{fig_id}-pane-{lang}" '
                f'aria-labelledby="{fig_id}-tab-{lang}" data-lang="{esc(lang)}">'
                f'<div class="paneflag">{esc(pane["label"])}</div>{code}</div>'
            )
        else:
            out.append(code)
    out.append("</figure>")
    return "\n".join(out)


def table_html(block, caption):
    out = ['<div class="tablewrap" tabindex="0">', "<table>"]
    if caption:
        out.append(f"<caption>{caption}</caption>")
    if block.get("head"):
        out.append(
            "<thead><tr>"
            + "".join(f'<th scope="col">{esc(h)}</th>' for h in block["head"])
            + "</tr></thead>"
        )
    out.append("<tbody>")
    for row in block["rows"]:
        cells = "".join(
            (
                f'<td class="{c["class"]}">{c["html"]}</td>'
                if c["class"]
                else f"<td>{c['html']}</td>"
            )
            for c in row
        )
        out.append(f"<tr>{cells}</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def meta_html(meta, site, conflicts_for):
    kind = site["kinds"][meta["kind"]]
    conf = site["confidences"][meta["confidence"]]
    status = site["example_statuses"][meta["example_status"]]
    chips = [
        f'<li><span class="badge badge-kind" title="{esc(kind["hint"])}">{esc(kind["label"])}</span></li>',
        f'<li><span class="badge badge-{meta["confidence"]}" title="{esc(conf["hint"])}">'
        f'{esc(conf["label"])}</span></li>',
        f'<li><span class="badge badge-status" title="{esc(status["hint"])}">'
        f'{esc(status["label"])}</span></li>',
    ]
    out = [f'<ul class="meta">{"".join(chips)}</ul>']

    if meta.get("caveat"):
        out.append(
            f'<p class="caveat"><strong>Область применимости.</strong> '
            f'{esc(" ".join(meta["caveat"].split()))}</p>'
        )
    if meta.get("versions"):
        out.append(
            f'<p class="versions"><strong>Версии.</strong> '
            f'{esc(" ".join(meta["versions"].split()))}</p>'
        )
    if conflicts_for:
        links = ", ".join(f'<a href="#s10">{esc(c)}</a>' for c in conflicts_for)
        out.append(
            f'<p class="conflicts-ref"><strong>Конфликтует:</strong> {links}</p>'
        )
    if meta.get("sources"):
        links = ", ".join(
            f'<a href="{esc(s["url"])}" rel="noopener noreferrer">{esc(s["title"])}</a>'
            for s in meta["sources"]
        )
        out.append(f'<p class="sources"><strong>Источники:</strong> {links}</p>')
    return "\n".join(out)


def principle_html(p, meta, site, conflicts_for):
    status = site["example_statuses"][meta["example_status"]]
    out = [
        f'<article class="principle" id="p{p["id"]}" data-keywords="{esc(p["keywords"])}" '
        f'data-kind="{meta["kind"]}" data-confidence="{meta["confidence"]}">',
        f'<div class="p-head"><span class="p-num">{p["id"]:02d}</span>'
        f'<h3>{p["title"]}</h3>'
        f'<a class="anchor" href="#p{p["id"]}" aria-label="Ссылка на принцип {p["id"]}">#</a></div>',
        meta_html(meta, site, conflicts_for),
    ]
    fig_n = 0
    for block in p["blocks"]:
        if block["type"] == "code":
            fig_n += 1
            out.append(
                figure_html(
                    block, f'p{p["id"]}f{fig_n}', status["label"], status["hint"]
                )
            )
        elif block["type"] == "table":
            out.append(table_html(block, None))
        elif block["type"] == "list":
            out.append(f'<ul>{block["html"]}</ul>')
        else:
            cls = {"lede": ' class="lede"', "note": ' class="note"'}.get(
                block["type"], ""
            )
            out.append(f'<p{cls}>{block["html"]}</p>')
    out.append("</article>")
    return "\n".join(out)


def main():
    site = load("site.yaml")
    meta_all = load("metadata.yaml")
    sections = load("sections.yaml")
    conflicts = load("conflicts.yaml")["conflicts"]
    principles = load_principles()
    count = len(principles)

    back = {}
    for row in conflicts:
        for pid in row["refs"]:
            back.setdefault(pid, []).append(row["left"])

    body, rail = [], []
    for sec in sections["sections"]:
        body.append(
            f'<section class="section" id="{sec["id"]}"'
            + (' data-always="1"' if sec["always"] else "")
            + ">"
        )
        body.append(
            f'<div class="section-head"><span class="numeral">{sec["numeral"]}</span>'
            f'<h2>{sec["title"]}</h2></div>'
        )

        subheads = {
            i["before"]: i["text"] for i in sec["intro"] if i["type"] == "subhead"
        }
        for item in sec["intro"]:
            if item["type"] == "note":
                body.append(f'<p class="note">{item["html"]}</p>')
            elif item["type"] == "text":
                body.append(f'<p class="section-lede">{item["html"]}</p>')

        if sec.get("generated") == "conflicts":
            rows = [
                [
                    {"html": esc(c["left"]), "class": ""},
                    {"html": esc(c["resolution"]), "class": ""},
                ]
                for c in conflicts
            ]
            body.append(
                table_html(
                    {"head": ["Конфликт", "Разрешение"], "rows": rows},
                    "Пары принципов, которые тянут в разные стороны, и способ разрешения",
                )
            )

        for pid in sec["principles"]:
            p = principles[pid]
            if f"p{pid}" in subheads:
                body.append(f'<h3 class="subhead">{esc(subheads[f"p{pid}"])}</h3>')
            meta = meta_all["principles"][pid]
            body.append(principle_html(p, meta, site, back.get(pid, [])))

        for item in sec["intro"]:
            if item["type"] == "closing":
                body.append(f'<p class="closing">{item["html"]}</p>')
        body.append("</section>")

        rail.append(f'<div class="rail-group" data-for="{sec["id"]}">')
        rail.append(
            f'<a href="#{sec["id"]}">{sec["numeral"]} · {esc(sec["title"])}</a>'
        )
        if sec["principles"]:
            rail.append("<ol>")
            for pid in sec["principles"]:
                p = principles[pid]
                rail.append(
                    f'<li data-for="p{pid}"><a href="#p{pid}">'
                    f'<span class="rail-num">{pid}</span> {esc(p["nav_label"])}</a></li>'
                )
            rail.append("</ol>")
        rail.append("</div>")

    langpick = ['<div class="langpick" role="group" aria-label="Язык примеров">']
    for lang in site["languages"]:
        langpick.append(
            f'<button type="button" data-lang="{lang["id"]}" '
            f'aria-pressed="{"true" if lang["id"] == "all" else "false"}">'
            f'{esc(lang["label"])}</button>'
        )
    langpick.append("</div>")

    hero = [
        f'<div class="eyebrow">{esc(site["hero"]["eyebrow"].format(count=count))}</div>',
        f'<h1>{esc(site["title"])}</h1>',
    ]
    hero += [f"<p>{para}</p>" for para in site["hero"]["paragraphs"]]
    hero.append(
        '<div class="chips">'
        + "".join(f'<span class="chip">{esc(c)}</span>' for c in site["hero"]["chips"])
        + "</div>"
    )

    footer = [
        f"<span>Справочник · {count} принципов</span>",
        "<span>Java · Rust · Go · Python 3.12+</span>",
        f'<span>Технический пересмотр: {esc(site["last_reviewed"])}</span>',
        f'<span><a href="{esc(site["repo"])}" rel="noopener noreferrer">Исходники '
        "и правки — на GitHub</a></span>",
    ]

    page = (ROOT / "templates" / "page.html").read_text(encoding="utf-8")
    for token, value in {
        "__TITLE__": esc(site["title"]),
        "__DESCRIPTION__": esc(" ".join(site["description"].split())),
        "__OG_DESCRIPTION__": esc(
            " ".join(site["og_description"].format(count=count).split())
        ),
        "__BRAND__": f'{esc(site["brand"][0])} <span>{esc(site["brand"][1])}</span>',
        "__LANGPICK__": "\n".join(langpick),
        "__RAIL__": "\n".join(rail),
        "__HERO__": "\n".join(hero),
        "__SECTIONS__": "\n\n".join(body),
        "__FOOTER__": "\n".join(footer),
    }.items():
        page = page.replace(token, value)

    (ROOT / "index.html").write_text(page, encoding="utf-8")
    figures = sum(
        1 for p in principles.values() for b in p["blocks"] if b["type"] == "code"
    )
    panes = sum(
        len(b["panes"])
        for p in principles.values()
        for b in p["blocks"]
        if b["type"] == "code"
    )
    print(
        f"built index.html — {count} принципов, {figures} фигур, {panes} панелей кода"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

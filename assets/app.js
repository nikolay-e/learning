(() => {
  const LANG_KEY = "principles:lang";
  const THEME_KEY = "principles:theme";
  const LANGS = ["java", "rust", "go", "python"];
  const LANG_NAMES = {
    java: "Java",
    rust: "Rust",
    go: "Go",
    python: "Python",
    sql: "SQL",
    kotlin: "Kotlin",
    bash: "shell",
    yaml: "YAML",
    protobuf: "Protobuf",
  };
  const langName = (id) => LANG_NAMES[id] || id;

  /* ---------- theme ---------- */

  const root = document.documentElement;
  const themeBtn = document.getElementById("theme-toggle");
  const storedTheme = localStorage.getItem(THEME_KEY);
  if (storedTheme) root.dataset.theme = storedTheme;
  else if (window.matchMedia("(prefers-color-scheme: light)").matches)
    root.dataset.theme = "light";

  function syncTheme() {
    const light = root.dataset.theme === "light";
    themeBtn.setAttribute("aria-pressed", String(light));
    themeBtn.setAttribute(
      "aria-label",
      light ? "Включить тёмную тему" : "Включить светлую тему",
    );
  }
  themeBtn.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    localStorage.setItem(THEME_KEY, root.dataset.theme);
    syncTheme();
  });
  syncTheme();

  /* ---------- code panes ---------- */

  const figures = [...document.querySelectorAll(".code[data-multi]")];
  const copyStatus = document.getElementById("copy-status");

  function showPane(fig, lang, { global = false } = {}) {
    const panes = [...fig.querySelectorAll(".codepane")];
    const available = panes.map((p) => p.dataset.lang);
    const missing = global && lang !== "all" && !available.includes(lang);
    const target = lang === "all" ? null : missing ? available[0] : lang;

    panes.forEach((p) => {
      p.hidden = target !== null && p.dataset.lang !== target;
    });
    fig.classList.toggle("allmode", target === null && panes.length > 1);

    const tabs = [...fig.querySelectorAll(".langtab")];
    tabs.forEach((t) => {
      const on = target !== null && t.dataset.lang === target;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    });
    // клавиатура должна иметь точку входа даже когда выбран режим «Все»
    if (target === null && tabs.length) tabs[0].tabIndex = 0;

    // Молчаливый fallback — худший вариант: если примера на выбранном языке нет,
    // страница обязана это сказать, а не подсунуть другой язык под тем же ярлыком.
    const note = fig.querySelector(".fallback-note");
    if (note) {
      note.hidden = !missing;
      note.textContent = missing
        ? `Примера на ${langName(lang)} здесь нет — показан ${langName(available[0])}.`
        : "";
    }
  }

  function applyLang(lang) {
    figures.forEach((fig) => showPane(fig, lang, { global: true }));
    document.querySelectorAll(".langpick button").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });
    localStorage.setItem(LANG_KEY, lang);
  }

  figures.forEach((fig) => {
    const tabs = [...fig.querySelectorAll(".langtab")];
    tabs.forEach((tab, i) => {
      tab.addEventListener("click", () => showPane(fig, tab.dataset.lang));
      tab.addEventListener("keydown", (e) => {
        const delta =
          e.key === "ArrowRight"
            ? 1
            : e.key === "ArrowLeft"
              ? -1
              : e.key === "Home"
                ? -i
                : e.key === "End"
                  ? tabs.length - 1 - i
                  : 0;
        if (!delta) return;
        e.preventDefault();
        const next = tabs[(i + delta + tabs.length) % tabs.length];
        showPane(fig, next.dataset.lang);
        next.focus();
      });
    });
  });

  document.querySelectorAll(".langpick button").forEach((b) => {
    b.addEventListener("click", () => applyLang(b.dataset.lang));
  });

  const savedLang = localStorage.getItem(LANG_KEY);
  applyLang(
    LANGS.includes(savedLang) || savedLang === "all" ? savedLang : "all",
  );

  /* ---------- language picker follows the viewport ---------- */

  const langpick = document.querySelector(".langpick");
  const slotTop = document.getElementById("langpick-slot-top");
  const slotRail = document.getElementById("langpick-slot-rail");
  const narrow = window.matchMedia("(max-width: 620px)");
  const placeLangpick = () =>
    (narrow.matches ? slotRail : slotTop).appendChild(langpick);
  narrow.addEventListener("change", placeLangpick);
  placeLangpick();

  /* ---------- copy ---------- */

  document.querySelectorAll(".copy").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const fig = btn.closest(".code");
      const panes = [...fig.querySelectorAll(".codepane")].filter(
        (p) => !p.hidden,
      );
      // фигуры без табов панелей не имеют — копируем саму фигуру
      const scopes = panes.length ? panes : [fig];
      const text = scopes
        .map((p) => {
          const code = p.querySelector("pre code").innerText;
          if (scopes.length === 1) return code;
          // textContent, а не innerText: innerText отдаёт текст после
          // text-transform: uppercase, и ярлык перестаёт совпадать с исходным
          const label =
            p.querySelector(".paneflag")?.textContent?.trim() ||
            p.dataset.lang ||
            "пример";
          return `// --- ${label} ---\n${code}`;
        })
        .join("\n\n");
      try {
        await navigator.clipboard.writeText(text);
        const was = btn.textContent;
        btn.textContent = "скопировано";
        copyStatus.textContent = "Код скопирован в буфер обмена";
        setTimeout(() => {
          btn.textContent = was;
          copyStatus.textContent = "";
        }, 1400);
      } catch {
        btn.textContent = "не вышло";
        copyStatus.textContent = "Не удалось скопировать";
      }
    });
  });

  /* ---------- search ---------- */

  const search = document.getElementById("search");
  const searchStatus = document.getElementById("search-status");
  const articles = [...document.querySelectorAll(".principle")];
  const sections = [...document.querySelectorAll(".section")];
  const emptyMsg = document.getElementById("empty");
  const subheads = [...document.querySelectorAll(".subhead")];

  const railItemFor = new Map();
  document
    .querySelectorAll(".rail-group li")
    .forEach((li) => railItemFor.set(li.dataset.for, li));
  const railGroupFor = new Map();
  document
    .querySelectorAll(".rail-group")
    .forEach((g) => railGroupFor.set(g.dataset.for, g));

  const haystack = new Map(
    articles.map((a) => [
      a,
      `${a.dataset.keywords || ""} ${a.textContent}`.toLowerCase(),
    ]),
  );
  const sectionHay = new Map(
    sections.map((s) => [
      s,
      `${s.querySelector(".section-head").textContent} ${s.textContent}`.toLowerCase(),
    ]),
  );

  function matches(hay, tokens) {
    return tokens.every((t) => hay.includes(t));
  }

  function runSearch(raw, { push = true } = {}) {
    const q = raw.trim().toLowerCase();
    const tokens = q ? q.split(/\s+/) : [];
    let hits = 0;

    articles.forEach((a) => {
      const hit = !tokens.length || matches(haystack.get(a), tokens);
      a.hidden = !hit;
      if (hit) hits++;
      const item = railItemFor.get(a.id);
      if (item) item.hidden = !hit;
    });

    sections.forEach((s) => {
      const anyVisible = [...s.querySelectorAll(".principle")].some(
        (a) => !a.hidden,
      );
      const ownMatch =
        s.dataset.always === "1" &&
        (!tokens.length || matches(sectionHay.get(s), tokens));
      s.hidden = !anyVisible && !ownMatch;
      if (ownMatch) hits++;
      const group = railGroupFor.get(s.id);
      if (group) group.hidden = s.hidden;
    });

    subheads.forEach((h) => (h.hidden = tokens.length > 0));
    if (emptyMsg) emptyMsg.hidden = !tokens.length || hits > 0;
    searchStatus.textContent = tokens.length
      ? `Найдено разделов и принципов: ${hits}`
      : "";

    if (push) {
      const url = new URL(location.href);
      if (q) url.searchParams.set("q", raw.trim());
      else url.searchParams.delete("q");
      history.replaceState(null, "", url);
    }
  }

  search.addEventListener("input", () => runSearch(search.value));
  search.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      search.value = "";
      runSearch("");
      search.blur();
    }
  });

  const isEditable = (el) =>
    el &&
    (el.isContentEditable ||
      ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));

  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !isEditable(document.activeElement)) {
      e.preventDefault();
      search.focus();
    }
  });

  const initialQuery = new URL(location.href).searchParams.get("q");
  if (initialQuery) {
    search.value = initialQuery;
    runSearch(initialQuery, { push: false });
  }

  /* ---------- rail toggle (mobile) ---------- */

  const rail = document.getElementById("rail");
  const railToggle = document.getElementById("rail-toggle");
  railToggle.addEventListener("click", () => {
    const open = rail.classList.toggle("open");
    railToggle.setAttribute("aria-expanded", String(open));
  });
  rail.addEventListener("click", (e) => {
    if (e.target.tagName === "A" && window.innerWidth <= 1080) {
      rail.classList.remove("open");
      railToggle.setAttribute("aria-expanded", "false");
    }
  });

  /* ---------- scroll spy ---------- */

  const links = new Map();
  document
    .querySelectorAll(".rail-group li a")
    .forEach((a) => links.set(a.getAttribute("href").slice(1), a));

  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const link = links.get(entry.target.id);
        if (!link || !entry.isIntersecting) return;
        links.forEach((l) => l.classList.remove("current"));
        link.classList.add("current");
        const box = link.getBoundingClientRect();
        const railBox = rail.getBoundingClientRect();
        if (box.top < railBox.top || box.bottom > railBox.bottom) {
          link.scrollIntoView({ block: "nearest" });
        }
      });
    },
    { rootMargin: "-80px 0px -70% 0px", threshold: 0 },
  );
  articles.forEach((a) => spy.observe(a));

  /* ---------- highlight ---------- */

  if (window.hljs) {
    hljs.configure({ ignoreUnescapedHTML: true });
    document
      .querySelectorAll("pre code")
      .forEach((el) => hljs.highlightElement(el));
  }
})();

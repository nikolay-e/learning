(() => {
  const LANG_KEY = "principles:lang";
  const THEME_KEY = "principles:theme";
  const LANGS = ["java", "rust", "go", "python"];

  /* ---------- theme ---------- */

  const root = document.documentElement;
  const storedTheme = localStorage.getItem(THEME_KEY);
  if (storedTheme) root.dataset.theme = storedTheme;
  else if (window.matchMedia("(prefers-color-scheme: light)").matches)
    root.dataset.theme = "light";

  document.getElementById("theme-toggle").addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    localStorage.setItem(THEME_KEY, root.dataset.theme);
  });

  /* ---------- code panes ---------- */

  const figures = [...document.querySelectorAll(".code[data-multi]")];

  function showPane(fig, lang) {
    const panes = [...fig.querySelectorAll(".codepane")];
    const available = panes.map((p) => p.dataset.lang);
    const target =
      lang === "all" ? null : available.includes(lang) ? lang : available[0];

    panes.forEach((p) => {
      p.hidden = target !== null && p.dataset.lang !== target;
    });
    fig.classList.toggle("allmode", target === null && panes.length > 1);
    fig.querySelectorAll(".langtab").forEach((t) => {
      t.setAttribute(
        "aria-selected",
        String(target !== null && t.dataset.lang === target),
      );
    });
  }

  function applyLang(lang) {
    figures.forEach((fig) => showPane(fig, lang));
    document.querySelectorAll(".langpick button").forEach((b) => {
      b.setAttribute("aria-pressed", String(b.dataset.lang === lang));
    });
    localStorage.setItem(LANG_KEY, lang);
  }

  figures.forEach((fig) => {
    fig.querySelectorAll(".langtab").forEach((tab) => {
      tab.addEventListener("click", () => showPane(fig, tab.dataset.lang));
    });
  });

  document.querySelectorAll(".langpick button").forEach((b) => {
    b.addEventListener("click", () => applyLang(b.dataset.lang));
  });

  const savedLang = localStorage.getItem(LANG_KEY);
  applyLang(
    LANGS.includes(savedLang) || savedLang === "all" ? savedLang : "all",
  );

  /* ---------- copy ---------- */

  document.querySelectorAll(".copy").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const fig = btn.closest(".code");
      const visible = [...fig.querySelectorAll(".codepane")].filter(
        (p) => !p.hidden,
      );
      const text = visible
        .map((p) => p.querySelector("code").innerText)
        .join("\n\n");
      try {
        await navigator.clipboard.writeText(text);
        const was = btn.textContent;
        btn.textContent = "скопировано";
        setTimeout(() => (btn.textContent = was), 1400);
      } catch {
        btn.textContent = "не вышло";
      }
    });
  });

  /* ---------- search ---------- */

  const search = document.getElementById("search");
  const articles = [...document.querySelectorAll(".principle")];
  const sections = [...document.querySelectorAll(".section")];
  const railItems = [...document.querySelectorAll(".rail-group li")];
  const emptyMsg = document.getElementById("empty");
  const subheads = [...document.querySelectorAll(".subhead")];

  const haystack = new Map(
    articles.map((a) => [
      a,
      (a.dataset.keywords || "") + " " + a.textContent.toLowerCase(),
    ]),
  );

  function runSearch(qRaw) {
    const q = qRaw.trim().toLowerCase();
    let hits = 0;

    articles.forEach((a) => {
      const match = !q || haystack.get(a).includes(q);
      a.hidden = !match;
      if (match) hits++;
      const item = railItems.find((li) => li.dataset.for === a.id);
      if (item) item.hidden = !match;
    });

    sections.forEach((s) => {
      const anyVisible = [...s.querySelectorAll(".principle")].some(
        (a) => !a.hidden,
      );
      const ownMatch =
        s.dataset.always === "1" &&
        (!q || s.textContent.toLowerCase().includes(q));
      s.hidden = !anyVisible && !ownMatch;
      if (ownMatch) hits++;
      const group = document.querySelector(`.rail-group[data-for="${s.id}"]`);
      if (group) group.hidden = s.hidden;
    });

    subheads.forEach((h) => (h.hidden = Boolean(q)));
    if (emptyMsg) emptyMsg.hidden = !q || hits > 0;
  }

  search.addEventListener("input", () => runSearch(search.value));
  search.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      search.value = "";
      runSearch("");
      search.blur();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== search) {
      e.preventDefault();
      search.focus();
    }
  });

  /* ---------- rail toggle (mobile) ---------- */

  const rail = document.getElementById("rail");
  document
    .getElementById("rail-toggle")
    .addEventListener("click", () => rail.classList.toggle("open"));
  rail.addEventListener("click", (e) => {
    if (e.target.tagName === "A" && window.innerWidth <= 1080)
      rail.classList.remove("open");
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
        if (!link) return;
        if (entry.isIntersecting) {
          links.forEach((l) => l.classList.remove("current"));
          link.classList.add("current");
          const box = link.getBoundingClientRect();
          const railBox = rail.getBoundingClientRect();
          if (box.top < railBox.top || box.bottom > railBox.bottom) {
            link.scrollIntoView({ block: "nearest" });
          }
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

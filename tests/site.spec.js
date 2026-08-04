import { expect, test } from "@playwright/test";

const isMobile = (info) => info.project.name === "mobile";

// Playwright даёт каждому тесту свой BrowserContext, поэтому localStorage уже
// изолирован — чистить его в beforeEach нельзя: initScript срабатывает и на
// reload и ломает как раз те тесты, которые проверяют сохранение состояния.
test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("каждый принцип попал в оглавление и в разделы, ссылки живые", async ({
  page,
}) => {
  const result = await page.evaluate(() => {
    const domIds = [...document.querySelectorAll(".principle")].map(
      (a) => a.id,
    );
    const railIds = [...document.querySelectorAll(".rail-group li")].map(
      (li) => li.dataset.for,
    );
    const anchors = new Set(
      [...document.querySelectorAll("[id]")].map((el) => el.id),
    );
    const dead = [...document.querySelectorAll('a[href^="#"]')]
      .map((a) => a.getAttribute("href").slice(1))
      .filter((h) => !anchors.has(h));
    return {
      count: domIds.length,
      sameOrder: JSON.stringify(domIds) === JSON.stringify(railIds),
      dead,
      // сплошность нумерации (с учётом retired) проверяет validate.py по
      // исходнику; странице остаётся не выдать один номер дважды
      duplicates: domIds.filter((id, i) => domIds.indexOf(id) !== i),
    };
  });
  expect(result.count).toBeGreaterThan(0);
  expect(result.sameOrder).toBe(true);
  expect(result.dead).toEqual([]);
  expect(result.duplicates).toEqual([]);
});

test("у каждого принципа проставлен тип утверждения и уверенность", async ({
  page,
}) => {
  const missing = await page.evaluate(() =>
    [...document.querySelectorAll(".principle")]
      .filter(
        (a) =>
          !a.dataset.kind ||
          !a.dataset.confidence ||
          a.querySelectorAll(".meta .badge").length < 3,
      )
      .map((a) => a.id),
  );
  expect(missing).toEqual([]);
});

test("подсветка синтаксиса применяется ко всем блокам", async ({ page }) => {
  const stats = await page.evaluate(() => {
    const all = [...document.querySelectorAll("pre code")];
    return {
      total: all.length,
      lit: all.filter((c) => c.classList.contains("hljs")).length,
    };
  });
  expect(stats.total).toBeGreaterThan(100);
  expect(stats.lit).toBe(stats.total);
});

test("выбор языка не подменяет пример молча", async ({ page }, info) => {
  if (isMobile(info)) {
    await page.locator("#rail-toggle").click();
  }
  await page.locator('.langpick button[data-lang="go"]').click();

  const audit = await page.evaluate(() =>
    [...document.querySelectorAll(".code[data-multi]")].map((fig) => {
      const visible = [...fig.querySelectorAll(".codepane")].filter(
        (p) => !p.hidden,
      );
      const note = fig.querySelector(".fallback-note");
      return {
        langs: visible.map((p) => p.dataset.lang),
        noteShown: note ? !note.hidden : false,
      };
    }),
  );
  for (const fig of audit) {
    expect(fig.langs).toHaveLength(1);
    // либо это действительно Go, либо страница прямо сказала, что это подмена
    expect(fig.langs[0] === "go" || fig.noteShown).toBe(true);
  }
});

test("выбор языка переживает перезагрузку", async ({ page }, info) => {
  if (isMobile(info)) await page.locator("#rail-toggle").click();
  await page.locator('.langpick button[data-lang="rust"]').click();
  await page.reload();
  if (isMobile(info)) await page.locator("#rail-toggle").click();
  await expect(
    page.locator('.langpick button[data-lang="rust"]'),
  ).toHaveAttribute("aria-pressed", "true");
});

test("тема переключается и сохраняется", async ({ page }) => {
  const toggle = page.locator("#theme-toggle");
  const before = await page.evaluate(
    () => document.documentElement.dataset.theme,
  );
  await toggle.click();
  const after = await page.evaluate(
    () => document.documentElement.dataset.theme,
  );
  expect(after).not.toBe(before);
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", after);
  await expect(toggle).toHaveAttribute("aria-label", /тему/);
});

test("фильтр сужает страницу, отражается в URL и сообщается скринридеру", async ({
  page,
}) => {
  await page.locator("#search").fill("watermark");
  await expect(page.locator(".principle:not([hidden])")).toHaveCount(1);
  await expect(page).toHaveURL(/\?q=watermark/);
  await expect(page.locator("#search-status")).toContainText("Найдено");

  await page.locator("#search").fill("zzzznotfound");
  await expect(page.locator("#empty")).toBeVisible();

  await page.locator("#search").fill("");
  await expect(page.locator("#empty")).toBeHidden();
});

test("фильтр восстанавливается из URL", async ({ page }) => {
  await page.goto("/?q=fencing");
  await expect(page.locator("#search")).toHaveValue("fencing");
  await expect(page.locator(".principle:not([hidden])")).toHaveCount(1);
});

test("поиск находит принцип по английскому синониму русского заголовка", async ({
  page,
}) => {
  await page.locator("#search").fill("robustness principle");
  await expect(page.locator("#p19")).toBeVisible();
});

test("копирование работает и на одноязычных карточках", async ({ page }) => {
  const copied = await page.evaluate(async () => {
    const seen = [];
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: async (t) => seen.push(t) },
    });
    document.querySelector("#p7 .copy").click();
    document.querySelector("#p1 .copy").click();
    await new Promise((r) => setTimeout(r, 50));
    return seen;
  });
  expect(copied[0].length).toBeGreaterThan(50);
  expect(copied[1].length).toBeGreaterThan(50);
});

test("в режиме «Все» скопированный код помечен языком", async ({
  page,
}, info) => {
  if (isMobile(info)) await page.locator("#rail-toggle").click();
  await page.locator('.langpick button[data-lang="all"]').click();
  const text = await page.evaluate(async () => {
    let out = "";
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: async (t) => (out = t) },
    });
    document.querySelector("#p1 .copy").click();
    await new Promise((r) => setTimeout(r, 50));
    return out;
  });
  expect(text).toContain("// --- Java ---");
  expect(text).toContain("// --- Rust ---");
});

test("табы языков доступны с клавиатуры", async ({ page }) => {
  const fig = page.locator("#p1 .code[data-multi]").first();
  const tabs = fig.locator(".langtab");
  await tabs.first().click();
  await expect(tabs.first()).toHaveAttribute("aria-selected", "true");
  await tabs.first().press("ArrowRight");
  await expect(tabs.nth(1)).toHaveAttribute("aria-selected", "true");
  await expect(tabs.nth(1)).toBeFocused();
});

test("активный таб языка видно, а не только слышно", async ({ page }) => {
  const fig = page.locator("#p1 .code[data-multi]").first();
  await fig.locator(".langtab").first().click();
  // курсор остаётся на кнопке после click(), и :hover подделывает выделение —
  // без увода мыши тест зелёный даже когда правило выбора мёртвое
  await page.mouse.move(0, 0);
  const [on, off] = await Promise.all([
    fig
      .locator('.langtab[aria-selected="true"]')
      .evaluate((el) => getComputedStyle(el).backgroundColor),
    fig
      .locator('.langtab[aria-selected="false"]')
      .first()
      .evaluate((el) => getComputedStyle(el).backgroundColor),
  ]);
  expect(on).not.toBe(off);
});

test("двойной клик по «копировать» не оставляет кнопку залипшей", async ({
  page,
}) => {
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: async () => {} },
    });
  });
  const btn = page.locator("#p1 .copy");
  const label = (await btn.textContent()).trim();
  await btn.click();
  await btn.click();
  await expect(btn).toHaveText(label, { timeout: 4000 });
});

test("тема применяется до загрузки app.js", async ({ context, page }) => {
  await context.addInitScript(() =>
    localStorage.setItem("principles:theme", "light"),
  );
  // если app.js не загрузился, а тема всё равно светлая — значит её выставил
  // скрипт в <head>, то есть вспышки тёмной темы не будет
  await page.route("**/assets/app.js", (route) => route.abort());
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("страница работает, когда localStorage запрещён", async ({
  context,
  page,
}) => {
  await context.addInitScript(() => {
    const boom = () => {
      throw new DOMException("denied", "SecurityError");
    };
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get: () => ({ getItem: boom, setItem: boom, removeItem: boom }),
    });
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  // поиск инициализируется последним: работает он — значит скрипт дожил до конца
  await page.locator("#search").fill("outbox");
  await expect(page.locator("#empty")).toBeHidden();
  await expect(page.locator(".principle:not([hidden])").first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("мобильное меню открывается и сообщает состояние", async ({
  page,
}, info) => {
  test.skip(!isMobile(info), "только мобильный проект");
  const toggle = page.locator("#rail-toggle");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator("#rail .langpick")).toBeVisible();
});

test("страница не скроллится по горизонтали", async ({ page }) => {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - window.innerWidth,
  );
  expect(overflow).toBeLessThanOrEqual(0);
});

test("в консоли нет ошибок", async ({ page }, info) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.reload({ waitUntil: "networkidle" });
  // обработчики падают на взаимодействии, а не на загрузке, поэтому проверка
  // привязана к реальным действиям, а не к произвольной паузе
  if (isMobile(info)) await page.locator("#rail-toggle").click();
  await page.locator('.langpick button[data-lang="go"]').click();
  await page.locator("#p1 .langtab").first().click();
  await page.locator("#search").fill("outbox");
  await expect(page.locator("#empty")).toBeHidden();
  expect(errors).toEqual([]);
});

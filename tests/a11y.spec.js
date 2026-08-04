import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// axe гоняем внутри Playwright, а не через @axe-core/cli: тот тянет системный
// Chrome + ChromeDriver и разъезжается по версиям на любой машине.
const scan = (page) =>
  new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();

test("страница проходит axe в тёмной теме", async ({ page }) => {
  await page.goto("/");
  const results = await scan(page);
  expect(
    results.violations.map((v) => `${v.id}: ${v.nodes.length} узлов`),
  ).toEqual([]);
});

test("страница проходит axe в светлой теме", async ({ page }) => {
  await page.goto("/");
  await page.locator("#theme-toggle").click();
  const results = await scan(page);
  expect(
    results.violations.map((v) => `${v.id}: ${v.nodes.length} узлов`),
  ).toEqual([]);
});

test("страница проходит axe с активным фильтром", async ({ page }) => {
  await page.goto("/?q=outbox");
  const results = await scan(page);
  expect(
    results.violations.map((v) => `${v.id}: ${v.nodes.length} узлов`),
  ).toEqual([]);
});

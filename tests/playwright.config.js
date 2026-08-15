import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  // Playwright берёт половину ядер: на 14-ядерной машине это семь Chromium
  // одновременно, и на 48 коротких тестов с четырьмя прогонами axe по
  // документу в сотню статей браузер успевает умереть — «browser.newContext:
  // Target page, context or browser has been closed» в случайном тесте
  // desktop-проекта. Измерено: 3 падения на 15 прогонов при семи воркерах,
  // 0 на 15 при четырёх. Это не retries — упавший так тест не сообщает о
  // странице ничего, и прятать его повтором значило бы приучать читать
  // красное как норму. На двухъядерном раннере воркер и так один.
  workers: process.env.CI ? undefined : 4,
  reporter: process.env.CI ? "html" : "list",
  use: {
    baseURL: "http://127.0.0.1:8777",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    // Pixel 7 — chromium-эмуляция: CI качает один браузер вместо двух
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: "python3 -m http.server 8777",
    url: "http://127.0.0.1:8777",
    reuseExistingServer: !process.env.CI,
    cwd: "..",
  },
});

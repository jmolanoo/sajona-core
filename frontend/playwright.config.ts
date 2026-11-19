import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60000,
  retries: 0,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:8089",
    headless: true,
    viewport: { width: 390, height: 844 },
    serviceWorkers: "allow",
    launchOptions: {
      executablePath:
        "/home/molano/.cache/ms-playwright/chromium_headless_shell-1254/chrome-headless-shell-linux64/chrome-headless-shell",
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    },
  },
});

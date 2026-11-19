import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("SAJONA Núcleo PWA (Módulos 1–3 + Dashboard) E2E", () => {
  test("flujo integral online, offline en los 3 módulos + dashboard, reapertura, auto-sync, conflictos y WCAG", async ({
    browser,
    request,
    baseURL,
  }) => {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      serviceWorkers: "allow",
    });
    const page = await context.newPage();

    // 1. Acceso inicial con red + Auditoría WCAG Login
    await page.goto(baseURL!);
    await expect(page.getByRole("heading", { name: "SAJONA ADE" })).toBeVisible();
    const axeLogin = await new AxeBuilder({ page }).analyze();
    expect(axeLogin.violations.filter((v) => v.impact === "critical")).toEqual([]);

    await page.getByLabel(/Usuario o Correo/i).fill("jefe");
    await page.getByLabel(/Contraseña/i).fill("SajonaJefe2026!");
    await page.getByRole("button", { name: "Ingresar" }).click();

    await expect(page.getByRole("heading", { name: "Dashboard Operativo SAJONA" })).toBeVisible();
    await expect(page.getByText("LOT-2026-030")).toBeVisible({ timeout: 15000 });

    // Service Worker activo + Manifest PWA
    const pwaInfo = await page.evaluate(async () => {
      const reg = await navigator.serviceWorker.ready;
      const man = await (await fetch("/manifest.webmanifest")).json();
      return { swActive: Boolean(reg.active), shortName: man.short_name };
    });
    expect(pwaInfo.swActive).toBe(true);
    expect(pwaInfo.shortName).toBe("SAJONA");

    const axeDash = await new AxeBuilder({ page }).analyze();
    expect(axeDash.violations.filter((v) => v.impact === "critical")).toEqual([]);

    // 2. Desconectar red -> trabajar offline en Módulo 1, Módulo 3 y Módulo 2
    await context.setOffline(true);
    await expect(page.getByText(/Modo Offline-First activo/i)).toBeVisible({ timeout: 5000 });

    // Módulo 1: Propagación
    await page.getByRole("button", { name: /Propag\./i }).click();
    await expect(page.getByRole("heading", { name: /Módulo 1: Propagación/i })).toBeVisible();
    await page.getByRole("button", { name: "Nuevo" }).click();
    const offlineCode = `LOT-CORE-${Date.now().toString().slice(-5)}`;
    await page.getByLabel(/Id Lote/i).fill(offlineCode);
    await page.getByLabel(/Cantidad de Siembra/i).fill("60");
    await page.getByRole("button", { name: "Guardar" }).click();
    await expect(page.getByText(offlineCode).first()).toBeVisible();

    // Enviar directamente a Módulo 3 (Transplante Bolsa) como PLANTA_MADRE con alerta >20% merma
    const card = page.locator(".grid > div").filter({ hasText: offlineCode }).first();
    await card.getByRole("button", { name: /A Bolsa/i }).click();
    await expect(page.getByRole("heading", { name: "Registrar Transplante a Bolsa" })).toBeVisible();
    await page.getByLabel(/Tipo de Lote/i).selectOption("PLANTA_MADRE");
    await page.getByLabel(/Unidades a Bolsa/i).fill("50");
    await page.getByLabel(/Cantidad Buenas Sobrevivientes/i).fill("35");
    await expect(page.getByText(/ALERTA: MERMA > 20%/i)).toBeVisible();
    await page.getByRole("button", { name: "Guardar Transplante a Bolsa" }).click();
    await expect(page.getByText(`TP-${offlineCode}-1`)).toBeVisible();

    // 3. Cierre y reapertura total de pestaña SIN CONEXIÓN (Service Worker + IndexedDB)
    await page.close();
    const reopened = await context.newPage();
    await reopened.goto(baseURL!);
    await expect(reopened.getByRole("heading", { name: "Dashboard Operativo SAJONA" })).toBeVisible({
      timeout: 15000,
    });
    await expect(reopened.getByText(offlineCode).first()).toBeVisible();
    await expect(reopened.getByText(/Modo Offline-First activo/i)).toBeVisible();

    // 4. Recuperar red -> Auto-sync de toda la cola causal (Propagación + Bolsa + Bloque Madre + Unidades)
    await context.setOffline(false);
    await expect(
      reopened.getByRole("button", { name: /Estado de conexión y sincronización/i })
    ).toContainText(/En línea/i, { timeout: 20000 });

    await reopened.getByRole("button", { name: /Estado de conexión y sincronización/i }).click();
    await expect(reopened.getByText("Todo está sincronizado con el servidor")).toBeVisible({
      timeout: 15000,
    });
    await reopened.getByRole("button", { name: "Cerrar modal" }).click();

    // 5. Conflicto concurrente real entre servidor y cliente offline -> resolución en SyncCenterModal
    const loginB = await request.post(`${baseURL}/api/v1/auth/login`, {
      data: { identifier: "admin", password: "SajonaAdmin2026!" },
    });
    const { access_token: adminToken } = (await loginB.json()) as { access_token: string };
    const lotesB = (await (
      await request.get(`${baseURL}/api/v1/entities/propagacion`, {
        headers: { Authorization: `Bearer ${adminToken}` },
      })
    ).json()) as Array<{ id: string; codigo_lote: string }>;
    const targetB = lotesB.find((l) => l.codigo_lote === offlineCode)!;
    expect(targetB).toBeTruthy();

    const putB = await request.put(`${baseURL}/api/v1/entities/propagacion/${targetB.id}`, {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { ...targetB, observaciones: "Editado en servidor por Admin" },
    });
    expect(putB.status()).toBe(200);

    await context.setOffline(true);
    await reopened.getByRole("button", { name: /Propag\./i }).click();
    const editCard = reopened.locator(".grid > div").filter({ hasText: offlineCode }).first();
    await editCard.getByRole("button", { name: "Editar" }).click();
    await reopened.getByLabel(/Observaciones/i).fill("Editado offline en campo");
    await reopened.getByRole("button", { name: "Guardar" }).click();

    await context.setOffline(false);
    await expect(
      reopened.getByRole("button", { name: /Estado de conexión y sincronización/i })
    ).toContainText(/Conflicto/i, { timeout: 15000 });
    await reopened.getByRole("button", { name: /Estado de conexión y sincronización/i }).click();
    await expect(reopened.getByText("Tu cambio local")).toBeVisible();
    await reopened.getByRole("button", { name: "Conservar mis cambios" }).click();
    await expect(reopened.getByText("Todo está sincronizado con el servidor")).toBeVisible({
      timeout: 15000,
    });
    await reopened.getByRole("button", { name: "Cerrar modal" }).click();

    // 6. Escritorio 1280x800 + Planta Madre + Traza 360
    await reopened.setViewportSize({ width: 1280, height: 800 });
    await reopened.getByRole("button", { name: "Planta Madre" }).first().click();
    await expect(reopened.getByRole("heading", { name: /Módulo 2: Planta Madre/i })).toBeVisible();
    await expect(reopened.getByText(`Bloque ${offlineCode}`)).toBeVisible();

    await context.close();
  });
});

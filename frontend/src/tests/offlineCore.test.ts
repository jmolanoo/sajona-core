import "fake-indexeddb/auto";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { db } from "../db/schema";
import { queueLocalMutation, resolveOutboxConflict, syncNow } from "../db/syncEngine";
import {
  calcularSaldoPropagacion,
  calcularSupervivenciaBolsa,
  calcularTotalesExtraccion,
  calcularVivasEnBolsa,
} from "../domain/calculations";
import { computeLocalDashboardSummary } from "../domain/dashboardStats";
import type { Propagacion, RevisionBolsa, TransplanteBolsa } from "../domain/types";

describe("SAJONA Núcleo — Reglas puras y Dashboard Offline", () => {
  it("calcula saldo de propagación, supervivencia bolsa, alerta >20% y vivas tras revisión", () => {
    const lote: Propagacion = {
      id: "l1",
      version: 1,
      codigo_lote: "LOT-01",
      fecha_siembra: "2026-10-01",
      variedad_id: "v1",
      tipo_propagacion: "ESQUEJE",
      tipo_incorporacion: "PROPIA",
      proveedor: "",
      cantidad_material: 100,
      cantidad_plantas_madre: 10,
      bajas_propagacion: 5,
      estado_lote: "SIEMBRA",
      observaciones: "",
    };
    const tps: TransplanteBolsa[] = [
      {
        id: "t1",
        version: 1,
        lote_id: "l1",
        codigo_transplante: "TP-1",
        fecha_transplante: "2026-10-15",
        ubicacion_id: "u1",
        cama_o_mesa: "B1",
        cantidad_procesada: 40,
        cantidad_buenas: 30,
        cantidad_malas: 10,
        porcentaje_buenas: 75,
        porcentaje_malas: 25,
        alerta_merma: true,
        tipo_lote: "PLANTA_COMERCIAL",
        capacidad_bolsa: "1L",
        observaciones: "",
      },
    ];
    expect(calcularSaldoPropagacion(lote, tps)).toBe(55);

    const calc = calcularSupervivenciaBolsa(55, 50, 35);
    expect(calc.cantidad_malas).toBe(15);
    expect(calc.porcentaje_malas).toBe(30);
    expect(calc.alerta_merma).toBe(true);
    expect(calc.nuevo_estado_lote).toBe("EN_TRANSPLANTE");

    const revs: RevisionBolsa[] = [
      {
        id: "r1",
        version: 1,
        transplante_id: "t1",
        fecha_revision: "2026-10-20",
        fase: "ENRAIZAMIENTO",
        unidades_revisadas: 30,
        contador_buenos: 27,
        contador_malos: 3,
        tipo_complicacion: "Estrés",
        estado_sanitario: "OBSERVACION",
        observaciones: "",
      },
    ];
    expect(calcularVivasEnBolsa(tps[0], revs)).toBe(27);
  });

  it("calcula totales CV-09 y KPIs locales de Dashboard offline", () => {
    const tot = calcularTotalesExtraccion([
      { numero_planta: 15, esquejes: 30, semillas: 0 },
      { numero_planta: 16, esquejes: 0, semillas: 20 },
      { numero_planta: 17, esquejes: 7, semillas: 0 },
      { numero_planta: 18, esquejes: 0, semillas: 40 },
    ]);
    expect(tot.totalEsquejes).toBe(37);
    expect(tot.totalSemillas).toBe(60);
    expect(tot.totalGeneral).toBe(97);

    const dash = computeLocalDashboardSummary({
      propagaciones: [
        {
          id: "l1",
          version: 1,
          codigo_lote: "LOT-01",
          fecha_siembra: "2026-10-01",
          variedad_id: "v1",
          tipo_propagacion: "ESQUEJE",
          tipo_incorporacion: "PROPIA",
          proveedor: "",
          cantidad_material: 100,
          cantidad_plantas_madre: 0,
          bajas_propagacion: 0,
          estado_lote: "FINALIZADO",
          observaciones: "",
        },
      ],
      transplantes: [],
      revisiones: [],
      lotesMadre: [],
      unidadesMadre: [],
      extracciones: [],
      variedades: [
        {
          id: "v1",
          version: 1,
          nombre: "Cannatonic",
          quimiotipo: "Balanceado",
          dias_vegetativo_est: 21,
          dias_floracion_est: 56,
          descripcion: "",
          activo: true,
        },
      ],
    });
    expect(dash.kpi_propagacion.total_lotes).toBe(1);
    expect(dash.kpi_propagacion.saldo_disponible).toBe(100);
  });
});

describe("Motor Offline-First IndexedDB + Outbox Causal + Conflictos", () => {
  beforeEach(async () => {
    await db.delete();
    await db.open();
    vi.restoreAllMocks();
  });

  it("persiste cadena causal offline sin red y detecta/resuelve conflicto al sincronizar", async () => {
    const idLote = await queueLocalMutation(
      "propagacion",
      "CREATE",
      {
        codigo_lote: "LOT-OFFLINE-UNIT",
        fecha_siembra: "2026-11-10",
        variedad_id: "v1",
        tipo_propagacion: "ESQUEJE",
        tipo_incorporacion: "PROPIA",
        proveedor: "",
        cantidad_material: 80,
        cantidad_plantas_madre: 0,
        bajas_propagacion: 0,
        estado_lote: "SIEMBRA",
        observaciones: "",
      },
      { triggerBackground: false }
    );

    const out = await db.outbox_mutations.orderBy("seq").toArray();
    expect(out).toHaveLength(1);
    expect(out[0].entity_id).toBe(idLote);

    const localStored = await db.propagacion.get(idLote);
    expect(localStored?._local_sync_status).toBe("pending");

    // Simular conflicto del servidor en push
    vi.stubGlobal("navigator", { onLine: true });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/auth/refresh")) {
          return new Response(
            JSON.stringify({ access_token: "tok", token_type: "bearer", expires_in: 900, user: {} }),
            { status: 200 }
          );
        }
        if (url.includes("/sync/push")) {
          return new Response(
            JSON.stringify({
              server_cursor: "2026-11-19T00:00:00Z",
              results: [
                {
                  client_mutation_id: out[0].client_mutation_id,
                  entity_type: "propagacion",
                  entity_id: idLote,
                  status: "conflict",
                  message: "Versión desactualizada",
                  server_record: { ...localStored, version: 2, cantidad_material: 90 },
                },
              ],
            }),
            { status: 200 }
          );
        }
        return new Response(
          JSON.stringify({ server_cursor: "2026-11-19T00:00:01Z", changes: {} }),
          { status: 200 }
        );
      })
    );

    await syncNow(false);
    const conflictOut = await db.outbox_mutations.orderBy("seq").toArray();
    expect(conflictOut[0].status).toBe("conflict");

    await resolveOutboxConflict(conflictOut[0], "use_server");
    const afterResolve = await db.propagacion.get(idLote);
    expect(afterResolve?.version).toBe(2);
    expect(afterResolve?.cantidad_material).toBe(90);
    expect(afterResolve?._local_sync_status).toBe("synced");
  });
});

import type {
  DetallePlantaExtraccion,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
} from "./types";

export interface SupervivenciaCalculo {
  cantidad_malas: number;
  porcentaje_buenas: number;
  porcentaje_malas: number;
  alerta_merma: boolean;
  nuevo_saldo_lote: number;
  nuevo_estado_lote: "SIEMBRA" | "EN_TRANSPLANTE" | "FINALIZADO";
}

export function calcularSaldoPropagacion(
  lote: Propagacion,
  transplantes: TransplanteBolsa[],
  excludeTransplanteId?: string
): number {
  const procesado = transplantes
    .filter((t) => !t.deleted_at && t.lote_id === lote.id && t.id !== excludeTransplanteId)
    .reduce((acc, t) => acc + Number(t.cantidad_procesada || 0), 0);
  return Math.max(
    0,
    Number(lote.cantidad_material || 0) - Number(lote.bajas_propagacion || 0) - procesado
  );
}

export function calcularSupervivenciaBolsa(
  saldoDisponible: number,
  cantidadProcesada: number,
  cantidadBuenas: number
): SupervivenciaCalculo {
  if (cantidadProcesada <= 0) {
    throw new Error("La cantidad procesada debe ser mayor a cero.");
  }
  if (cantidadProcesada > saldoDisponible) {
    throw new Error(
      `Saldo insuficiente en lote (${saldoDisponible} disponibles vs ${cantidadProcesada} ingresadas).`
    );
  }
  if (cantidadBuenas < 0 || cantidadBuenas > cantidadProcesada) {
    throw new Error("Las unidades buenas deben estar entre 0 y la cantidad procesada.");
  }
  const cantidadMalas = cantidadProcesada - cantidadBuenas;
  const pctBuenas = Math.round((cantidadBuenas * 10000) / cantidadProcesada) / 100;
  const pctMalas = Math.round((100 - pctBuenas) * 100) / 100;
  const nuevoSaldo = saldoDisponible - cantidadProcesada;
  return {
    cantidad_malas: cantidadMalas,
    porcentaje_buenas: pctBuenas,
    porcentaje_malas: pctMalas,
    alerta_merma: pctMalas > 20,
    nuevo_saldo_lote: nuevoSaldo,
    nuevo_estado_lote: nuevoSaldo === 0 ? "FINALIZADO" : "EN_TRANSPLANTE",
  };
}

export function calcularVivasEnBolsa(
  transplante: TransplanteBolsa,
  revisiones: RevisionBolsa[]
): number {
  const bajasRev = revisiones
    .filter((r) => !r.deleted_at && r.transplante_id === transplante.id)
    .reduce((acc, r) => acc + Number(r.contador_malos || 0), 0);
  return Math.max(0, Number(transplante.cantidad_buenas || 0) - bajasRev);
}

export function calcularTotalesExtraccion(detalle: DetallePlantaExtraccion[]): {
  totalEsquejes: number;
  totalSemillas: number;
  totalGeneral: number;
} {
  let totalEsquejes = 0;
  let totalSemillas = 0;
  for (const row of detalle) {
    totalEsquejes += Math.max(0, Number(row.esquejes || 0));
    totalSemillas += Math.max(0, Number(row.semillas || 0));
  }
  return {
    totalEsquejes,
    totalSemillas,
    totalGeneral: totalEsquejes + totalSemillas,
  };
}

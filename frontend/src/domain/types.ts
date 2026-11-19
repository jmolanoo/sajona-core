export type RoleName = "ADMIN" | "JEFE_PROYECTO" | "OPERARIO" | "CONSULTA";
export type LocalSyncStatus = "synced" | "pending" | "conflict";

export interface SyncRecordBase {
  id: string;
  version: number;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string | null;
  client_mutation_id?: string | null;
  _local_sync_status?: LocalSyncStatus;
}

export interface Variedad extends SyncRecordBase {
  nombre: string;
  quimiotipo: string;
  dias_vegetativo_est: number;
  dias_floracion_est: number;
  descripcion: string;
  activo: boolean;
}

export interface Ubicacion extends SyncRecordBase {
  nombre: string;
  tipo: "INVERNADERO" | "CASA_MALLA" | "CUBICULO" | "ENRAIZAMIENTO" | "CAMPO_BASE";
  capacidad_unidades: number;
  activo: boolean;
}

export interface Funcionario extends SyncRecordBase {
  nombre: string;
  apellido: string;
  documento: string;
  email: string;
  telefono: string;
  cargo: string;
  activo: boolean;
}

export interface Propagacion extends SyncRecordBase {
  codigo_lote: string;
  fecha_siembra: string;
  variedad_id: string;
  ubicacion_id?: string | null;
  responsable_id?: string | null;
  tipo_propagacion: "ESQUEJE" | "SEMILLA" | "IN_VITRO";
  tipo_incorporacion: "PROPIA" | "COMPRADA";
  origen_extraccion_id?: string | null;
  proveedor: string;
  cantidad_material: number;
  cantidad_plantas_madre: number;
  bajas_propagacion: number;
  estado_lote: "SIEMBRA" | "EN_TRANSPLANTE" | "FINALIZADO";
  observaciones: string;
}

export interface TransplanteBolsa extends SyncRecordBase {
  lote_id: string;
  codigo_transplante: string;
  fecha_transplante: string;
  ubicacion_id: string;
  responsable_id?: string | null;
  cama_o_mesa: string;
  cantidad_procesada: number;
  cantidad_buenas: number;
  cantidad_malas: number;
  porcentaje_buenas: number;
  porcentaje_malas: number;
  alerta_merma: boolean;
  tipo_lote: "PLANTA_MADRE" | "PLANTA_COMERCIAL";
  capacidad_bolsa: string;
  promover_planta_madre?: boolean;
  observaciones: string;
}

export interface RevisionBolsa extends SyncRecordBase {
  transplante_id: string;
  fecha_revision: string;
  fase: "ENRAIZAMIENTO" | "BOLSA_INICIAL" | "ACLIMATACION";
  unidades_revisadas: number;
  contador_buenos: number;
  contador_malos: number;
  tipo_complicacion: string;
  estado_sanitario: "OPTIMO" | "OBSERVACION" | "CRITICO";
  responsable_id?: string | null;
  observaciones: string;
}

export interface LotePlantaMadre extends SyncRecordBase {
  lote_id: string;
  transplante_bolsa_id?: string | null;
  fecha_establecimiento: string;
  ubicacion_id?: string | null;
  cantidad_madres_inicial: number;
  cantidad_madres_activas: number;
  observaciones: string;
}

export interface UnidadPlantaMadre extends SyncRecordBase {
  lote_madre_id: string;
  numero_planta: number;
  codigo_planta: string;
  estado_planta: "ACTIVA" | "REPOSO" | "DESCARTADA";
  total_esquejes: number;
  total_semillas: number;
  ultima_extraccion?: string | null;
  observaciones: string;
}

export interface DetallePlantaExtraccion {
  unidad_id?: string | null;
  numero_planta: number;
  esquejes: number;
  semillas: number;
}

export interface ExtraccionMadre extends SyncRecordBase {
  lote_madre_id: string;
  fecha_transplante_ref: string;
  fecha_extraccion: string;
  responsable_id?: string | null;
  detalle_plantas: DetallePlantaExtraccion[];
  total_esquejes: number;
  total_semillas: number;
  lote_hijo_codigo?: string | null;
  observaciones: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: RoleName;
  full_name: string;
  funcionario_id?: string | null;
  is_active: boolean;
  must_change_password?: boolean;
  permissions: Record<string, string[]>;
}

export type CoreEntityType =
  | "variedades"
  | "ubicaciones"
  | "funcionarios"
  | "propagacion"
  | "transplante_bolsa"
  | "revisiones_bolsa"
  | "lotes_planta_madre"
  | "unidades_planta_madre"
  | "extracciones_madre";

export interface OutboxMutation {
  seq?: number;
  client_mutation_id: string;
  entity_type: CoreEntityType;
  entity_id: string;
  operation: "CREATE" | "UPDATE" | "DELETE";
  base_version: number;
  payload: Record<string, unknown>;
  status: "pending" | "conflict" | "rejected";
  error_message?: string;
  server_snapshot?: Record<string, unknown> | null;
  created_at: string;
}

export interface DashboardSummary {
  kpi_propagacion: {
    total_lotes: number;
    lotes_activos: number;
    lotes_finalizados: number;
    total_sembrado: number;
    bajas_propagacion: number;
    saldo_disponible: number;
  };
  kpi_transplante_bolsa: {
    total_transplantes: number;
    total_procesado: number;
    buenas_iniciales: number;
    malas_transplante: number;
    revisiones_realizadas: number;
    bajas_en_revision: number;
    vivas_en_bolsa: number;
    supervivencia_pct: number;
    lotes_en_alerta_merma: number;
  };
  kpi_planta_madre: {
    total_lotes_madre: number;
    total_unidades_madre: number;
    madres_activas: number;
    total_extracciones: number;
    total_esquejes: number;
    total_semillas: number;
    lotes_hijos_derivados: number;
  };
  alertas_merma: Array<{
    id: string;
    codigo_transplante: string;
    lote_id: string;
    porcentaje_malas: number;
    cantidad_malas: number;
  }>;
  supervivencia_por_transplante: Array<{
    codigo: string;
    tipo_lote: string;
    buenas_pct: number;
    malas_pct: number;
    alerta_merma: boolean;
  }>;
  distribucion_por_variedad: Array<{
    variedad: string;
    lotes: number;
    sembrado: number;
    buenas_bolsa: number;
  }>;
}

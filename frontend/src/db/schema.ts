import Dexie, { type Table } from "dexie";
import type {
  CoreEntityType,
  ExtraccionMadre,
  Funcionario,
  LotePlantaMadre,
  OutboxMutation,
  Propagacion,
  RevisionBolsa,
  TransplanteBolsa,
  Ubicacion,
  UnidadPlantaMadre,
  UserProfile,
  Variedad,
} from "../domain/types";

export interface OfflineSessionRecord {
  id: string;
  user: UserProfile;
  offline_grace_until: string;
  last_online_login: string;
}

export interface SyncMetaRecord {
  key: string;
  value: string;
}

export class SajonaCoreDexieDB extends Dexie {
  variedades!: Table<Variedad, string>;
  ubicaciones!: Table<Ubicacion, string>;
  funcionarios!: Table<Funcionario, string>;
  propagacion!: Table<Propagacion, string>;
  transplante_bolsa!: Table<TransplanteBolsa, string>;
  revisiones_bolsa!: Table<RevisionBolsa, string>;
  lotes_planta_madre!: Table<LotePlantaMadre, string>;
  unidades_planta_madre!: Table<UnidadPlantaMadre, string>;
  extracciones_madre!: Table<ExtraccionMadre, string>;
  outbox_mutations!: Table<OutboxMutation, number>;
  offline_session!: Table<OfflineSessionRecord, string>;
  sync_meta!: Table<SyncMetaRecord, string>;

  constructor() {
    super("sajona_core_db");
    this.version(1).stores({
      variedades: "id, nombre, updated_at, _local_sync_status",
      ubicaciones: "id, nombre, tipo, updated_at, _local_sync_status",
      funcionarios: "id, documento, updated_at, _local_sync_status",
      propagacion: "id, codigo_lote, fecha_siembra, variedad_id, estado_lote, updated_at, _local_sync_status",
      transplante_bolsa: "id, lote_id, fecha_transplante, tipo_lote, updated_at, _local_sync_status",
      revisiones_bolsa: "id, transplante_id, fecha_revision, updated_at, _local_sync_status",
      lotes_planta_madre: "id, lote_id, transplante_bolsa_id, updated_at, _local_sync_status",
      unidades_planta_madre: "id, lote_madre_id, numero_planta, estado_planta, updated_at, _local_sync_status",
      extracciones_madre: "id, lote_madre_id, fecha_extraccion, updated_at, _local_sync_status",
      outbox_mutations: "++seq, client_mutation_id, entity_type, entity_id, status",
      offline_session: "id",
      sync_meta: "key",
    });
  }

  tableFor(entityType: CoreEntityType): Table<any, string> {
    return this[entityType] as Table<any, string>;
  }
}

export const db = new SajonaCoreDexieDB();

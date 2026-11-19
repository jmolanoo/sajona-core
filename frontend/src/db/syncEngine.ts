import { apiClient } from "../api/client";
import type { CoreEntityType, OutboxMutation, SyncRecordBase } from "../domain/types";
import { db } from "./schema";

export interface SyncStatusSnapshot {
  pendingCount: number;
  conflictCount: number;
  rejectedCount: number;
  lastSyncAt: string | null;
  syncing: boolean;
  lastError: string | null;
}

interface SyncPushResult {
  client_mutation_id: string;
  entity_type: CoreEntityType;
  entity_id: string;
  status: "applied" | "duplicate" | "conflict" | "rejected";
  message: string;
  record?: Record<string, unknown> | null;
  server_record?: Record<string, unknown> | null;
}

const listeners = new Set<() => void>();
let syncingFlag = false;
let lastErrorMsg: string | null = null;
let retryTimer: number | null = null;
let backoffMs = 1500;

export function subscribeSync(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function notifySync(): void {
  for (const fn of listeners) fn();
}

export async function getSyncSnapshot(): Promise<SyncStatusSnapshot> {
  const all = await db.outbox_mutations.toArray();
  const meta = await db.sync_meta.get("last_sync_at");
  return {
    pendingCount: all.filter((m) => m.status === "pending").length,
    conflictCount: all.filter((m) => m.status === "conflict").length,
    rejectedCount: all.filter((m) => m.status === "rejected").length,
    lastSyncAt: meta?.value || null,
    syncing: syncingFlag,
    lastError: lastErrorMsg,
  };
}

export async function queueLocalMutation(
  entityType: CoreEntityType,
  operation: "CREATE" | "UPDATE" | "DELETE",
  record: Record<string, unknown> & { id?: string; version?: number },
  options: { triggerBackground?: boolean } = {}
): Promise<string> {
  const id = record.id || crypto.randomUUID();
  const now = new Date().toISOString();
  const mutId = crypto.randomUUID();
  const baseVersion = Number(record.version || 1);
  const tbl = db.tableFor(entityType);

  await db.transaction("rw", tbl, db.outbox_mutations, async () => {
    const existing = await tbl.get(id);
    const optimisticRow: SyncRecordBase & Record<string, unknown> = {
      ...record,
      id,
      version: existing ? Number(existing.version || baseVersion) : 1,
      created_at: (existing?.created_at as string) || now,
      updated_at: now,
      deleted_at: operation === "DELETE" ? now : null,
      client_mutation_id: mutId,
      _local_sync_status: "pending",
    };
    await tbl.put(optimisticRow);

    await db.outbox_mutations.add({
      client_mutation_id: mutId,
      entity_type: entityType,
      entity_id: id,
      operation,
      base_version: operation === "CREATE" ? 0 : baseVersion,
      payload: optimisticRow,
      status: "pending",
      created_at: now,
    });
  });

  notifySync();
  if (options.triggerBackground !== false && typeof navigator !== "undefined" && navigator.onLine) {
    void syncNow();
  }
  return id;
}

async function applyPushResults(results: SyncPushResult[]): Promise<void> {
  for (const r of results) {
    const out = await db.outbox_mutations
      .where("client_mutation_id")
      .equals(r.client_mutation_id)
      .first();
    const tbl = db.tableFor(r.entity_type);

    if (r.status === "applied" || r.status === "duplicate") {
      if (r.record) {
        await tbl.put({ ...(r.record as Record<string, unknown>), _local_sync_status: "synced" });
      }
      if (out?.seq !== undefined) {
        await db.outbox_mutations.delete(out.seq);
      }
    } else if (r.status === "conflict" && out?.seq !== undefined) {
      await db.outbox_mutations.update(out.seq, {
        status: "conflict",
        error_message: r.message,
        server_snapshot: r.server_record || null,
      });
      const localRec = await tbl.get(r.entity_id);
      if (localRec) {
        await tbl.put({ ...localRec, _local_sync_status: "conflict" });
      }
    } else if (r.status === "rejected" && out?.seq !== undefined) {
      await db.outbox_mutations.update(out.seq, {
        status: "rejected",
        error_message: r.message,
      });
    }
  }
}

export async function pullIncremental(forceFull = false): Promise<void> {
  const cursorRec = forceFull ? null : await db.sync_meta.get("server_cursor");
  const qs = cursorRec?.value ? `?since=${encodeURIComponent(cursorRec.value)}` : "";
  const resp = await apiClient.request<{
    server_cursor: string;
    changes: Record<CoreEntityType, Array<Record<string, unknown>>>;
  }>(`/api/v1/sync/pull${qs}`);

  const dirtyRows = await db.outbox_mutations.toArray();
  const protectedIds = new Set(dirtyRows.map((m) => `${m.entity_type}:${m.entity_id}`));

  for (const [entityType, records] of Object.entries(resp.changes) as Array<
    [CoreEntityType, Array<Record<string, unknown>>]
  >) {
    const tbl = db.tableFor(entityType);
    if (forceFull) {
      const existingAll = await tbl.toArray();
      const serverIds = new Set(records.map((r) => String(r.id)));
      for (const local of existingAll) {
        const key = `${entityType}:${local.id}`;
        if (!protectedIds.has(key) && !serverIds.has(String(local.id))) {
          await tbl.delete(String(local.id));
        }
      }
    }
    for (const rec of records) {
      const key = `${entityType}:${rec.id}`;
      if (!protectedIds.has(key)) {
        await tbl.put({ ...rec, _local_sync_status: "synced" });
      }
    }
  }

  const nowIso = new Date().toISOString();
  await db.sync_meta.put({ key: "server_cursor", value: resp.server_cursor });
  await db.sync_meta.put({ key: "last_sync_at", value: nowIso });
}

export async function syncNow(forceFullPull = false): Promise<boolean> {
  if (syncingFlag) return false;
  if (typeof navigator !== "undefined" && !navigator.onLine) return false;
  if (!apiClient.getAccessToken()) {
    const refreshed = await apiClient.refreshAccessToken();
    if (!refreshed) return false;
  }

  syncingFlag = true;
  lastErrorMsg = null;
  notifySync();

  try {
    const pending = (await db.outbox_mutations.orderBy("seq").toArray()).filter(
      (m) => m.status === "pending"
    );

    if (pending.length > 0) {
      const pushResp = await apiClient.request<{
        server_cursor: string;
        results: SyncPushResult[];
      }>("/api/v1/sync/push", {
        method: "POST",
        body: JSON.stringify({
          mutations: pending.map((m) => ({
            client_mutation_id: m.client_mutation_id,
            entity_type: m.entity_type,
            entity_id: m.entity_id,
            operation: m.operation,
            base_version: m.base_version,
            payload: m.payload,
          })),
        }),
      });
      await applyPushResults(pushResp.results);
    }

    await pullIncremental(forceFullPull);
    backoffMs = 1500;
    return true;
  } catch (err) {
    lastErrorMsg = err instanceof Error ? err.message : "Error de sincronización";
    if (typeof window !== "undefined") {
      if (retryTimer) window.clearTimeout(retryTimer);
      retryTimer = window.setTimeout(() => void syncNow(), backoffMs);
      backoffMs = Math.min(backoffMs * 2, 60000);
    }
    return false;
  } finally {
    syncingFlag = false;
    notifySync();
  }
}

export async function resolveOutboxConflict(
  mutation: OutboxMutation,
  resolution: "keep_local" | "use_server"
): Promise<void> {
  if (mutation.seq === undefined) return;
  const tbl = db.tableFor(mutation.entity_type);

  if (resolution === "use_server") {
    if (mutation.server_snapshot) {
      await tbl.put({ ...mutation.server_snapshot, _local_sync_status: "synced" });
    }
    await db.outbox_mutations.delete(mutation.seq);
    notifySync();
    return;
  }

  const serverVer = Number(mutation.server_snapshot?.version || mutation.base_version + 1);
  const updatedPayload = { ...mutation.payload, version: serverVer };
  await tbl.put({ ...updatedPayload, _local_sync_status: "pending" });
  await db.outbox_mutations.update(mutation.seq, {
    base_version: serverVer,
    payload: updatedPayload,
    status: "pending",
    error_message: undefined,
    server_snapshot: null,
  });
  notifySync();
  if (typeof navigator !== "undefined" && navigator.onLine) {
    await syncNow();
  }
}

export async function discardFailedMutation(mutation: OutboxMutation): Promise<void> {
  if (mutation.seq === undefined) return;
  await db.outbox_mutations.delete(mutation.seq);
  await pullIncremental(true).catch(() => undefined);
  notifySync();
}

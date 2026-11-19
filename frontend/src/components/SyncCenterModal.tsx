import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, WifiOff } from "lucide-react";
import { db } from "../db/schema";
import {
  discardFailedMutation,
  resolveOutboxConflict,
  subscribeSync,
  syncNow,
} from "../db/syncEngine";
import { useOnlineStatus, useSyncStatus } from "../db/useLocalData";
import type { OutboxMutation } from "../domain/types";
import { Modal } from "./UiPrimitives";

export const SyncCenterModal: React.FC<{ open: boolean; onClose: () => void }> = ({
  open,
  onClose,
}) => {
  const online = useOnlineStatus();
  const snap = useSyncStatus();
  const [mutations, setMutations] = useState<OutboxMutation[]>([]);

  useEffect(() => {
    const load = async () => setMutations(await db.outbox_mutations.orderBy("seq").toArray());
    if (open) void load();
    return subscribeSync(() => void load());
  }, [open]);

  const conflicts = mutations.filter((m) => m.status === "conflict");
  const rejected = mutations.filter((m) => m.status === "rejected");
  const pending = mutations.filter((m) => m.status === "pending");

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Centro de Sincronización Offline-First"
      subtitle="Estado de cola local IndexedDB, reintentos y conflictos de concurrencia"
      wide
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
          <div className="text-xs text-slate-600">Conectividad</div>
          <div className="text-sm font-bold text-slate-900 mt-1">
            {online ? "En línea" : "Sin conexión"}
          </div>
        </div>
        <div className="rounded-xl border border-amber-200 p-3 bg-amber-50">
          <div className="text-xs text-amber-800">Pendientes</div>
          <div className="text-lg font-bold text-amber-900">{snap.pendingCount}</div>
        </div>
        <div className="rounded-xl border border-red-200 p-3 bg-red-50">
          <div className="text-xs text-red-800">Conflictos</div>
          <div className="text-lg font-bold text-red-900">{snap.conflictCount}</div>
        </div>
        <div className="rounded-xl border border-slate-200 p-3 bg-slate-50">
          <div className="text-xs text-slate-600">Última Sync</div>
          <div className="text-xs font-semibold text-slate-800 mt-1">
            {snap.lastSyncAt ? new Date(snap.lastSyncAt).toLocaleString("es-CO") : "Sin sincronizar"}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={!online || snap.syncing}
          onClick={() => void syncNow(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-emerald-700 text-white disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${snap.syncing ? "animate-spin" : ""}`} />
          {online ? "Sincronizar ahora" : "Esperando conexión..."}
        </button>
        {!online && (
          <span className="inline-flex items-center gap-1.5 text-xs text-amber-800 font-medium">
            <WifiOff className="w-4 h-4" /> Tus cambios locales permanecen seguros en IndexedDB.
          </span>
        )}
      </div>

      {snap.lastError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800">
          Último aviso: {snap.lastError}
        </div>
      )}

      {conflicts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-red-800 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4" /> Conflictos detectados ({conflicts.length})
          </h3>
          {conflicts.map((m) => (
            <div key={m.seq} className="rounded-xl border border-red-300 bg-red-50/40 p-3 space-y-2">
              <div className="flex justify-between items-center text-xs font-semibold text-slate-800">
                <span>
                  {m.entity_type} • ID {m.entity_id.slice(0, 8)}
                </span>
                <span className="text-red-700">{m.error_message}</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                <div className="bg-white rounded-lg border border-slate-200 p-2">
                  <div className="font-bold text-slate-700 mb-1">Tu cambio local</div>
                  <pre className="whitespace-pre-wrap text-[11px] text-slate-600 overflow-x-auto">
                    {JSON.stringify(m.payload, null, 2).slice(0, 400)}
                  </pre>
                </div>
                <div className="bg-white rounded-lg border border-slate-200 p-2">
                  <div className="font-bold text-slate-700 mb-1">
                    Versión actual del servidor (v{String(m.server_snapshot?.version || "?")})
                  </div>
                  <pre className="whitespace-pre-wrap text-[11px] text-slate-600 overflow-x-auto">
                    {JSON.stringify(m.server_snapshot || {}, null, 2).slice(0, 400)}
                  </pre>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void resolveOutboxConflict(m, "keep_local")}
                  className="px-3 py-2 rounded-lg text-xs font-semibold bg-amber-700 text-white"
                >
                  Conservar mis cambios
                </button>
                <button
                  type="button"
                  onClick={() => void resolveOutboxConflict(m, "use_server")}
                  className="px-3 py-2 rounded-lg text-xs font-semibold border border-slate-300 bg-white text-slate-800"
                >
                  Usar versión del servidor
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {rejected.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-bold text-red-800">Mutaciones rechazadas ({rejected.length})</h3>
          {rejected.map((m) => (
            <div key={m.seq} className="rounded-lg border border-red-200 bg-white p-3 text-xs space-y-2">
              <div className="font-semibold text-slate-800">
                {m.entity_type} ({m.operation}): {m.error_message}
              </div>
              <button
                type="button"
                onClick={() => void discardFailedMutation(m)}
                className="px-3 py-1.5 rounded border border-red-300 text-red-700 font-semibold"
              >
                Descartar y restaurar servidor
              </button>
            </div>
          ))}
        </div>
      )}

      {pending.length > 0 && (
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-700 uppercase">Cola en espera ({pending.length})</h3>
          {pending.map((m) => (
            <div
              key={m.seq}
              className="flex items-center justify-between text-xs rounded-lg border border-amber-200 bg-amber-50/50 px-3 py-2"
            >
              <span>
                #{m.seq} {m.operation} • <strong>{m.entity_type}</strong>
              </span>
              <span className="text-slate-500">{new Date(m.created_at).toLocaleTimeString("es-CO")}</span>
            </div>
          ))}
        </div>
      )}

      {mutations.length === 0 && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-center space-y-1">
          <CheckCircle2 className="w-7 h-7 text-emerald-700 mx-auto" />
          <p className="text-sm font-bold text-emerald-900">Todo está sincronizado con el servidor</p>
          <p className="text-xs text-emerald-700">No existen mutaciones pendientes en IndexedDB.</p>
        </div>
      )}
    </Modal>
  );
};

import React from "react";
import { Download, FileSpreadsheet, FileText, Printer, X } from "lucide-react";
import type { LocalSyncStatus } from "../domain/types";
import { exportAsExcel, exportAsPdf, exportAsTxt } from "../utils/exporters";

export const SyncStatusBadge: React.FC<{ status?: LocalSyncStatus }> = ({ status }) => {
  if (status === "conflict") {
    return (
      <span className="inline-flex items-center whitespace-nowrap shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
        • Conflicto
      </span>
    );
  }
  if (status === "pending") {
    return (
      <span className="inline-flex items-center whitespace-nowrap shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
        • Pendiente
      </span>
    );
  }
  return (
    <span className="inline-flex items-center whitespace-nowrap shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
      • Sincronizado
    </span>
  );
};

export const Modal: React.FC<{
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  wide?: boolean;
  children: React.ReactNode;
}> = ({ open, title, subtitle, onClose, wide, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-950/60 p-0 sm:p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`w-full ${
          wide ? "sm:max-w-3xl" : "sm:max-w-xl"
        } max-h-[92vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl bg-white shadow-2xl border border-slate-200`}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-3 bg-white border-b border-slate-200 px-4 py-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">{title}</h2>
            {subtitle && <p className="text-xs text-slate-600 mt-0.5">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-4">{children}</div>
      </div>
    </div>
  );
};

export const ExportToolbar: React.FC<{
  title: string;
  columns: string[];
  rows: Array<Array<string | number>>;
}> = ({ title, columns, rows }) => (
  <div className="flex flex-wrap items-center gap-2">
    <button
      type="button"
      onClick={() => void exportAsExcel(title, columns, rows)}
      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-emerald-300 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
    >
      <FileSpreadsheet className="w-4 h-4" /> Excel
    </button>
    <button
      type="button"
      onClick={() => exportAsTxt(title, columns, rows)}
      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
    >
      <FileText className="w-4 h-4" /> TXT
    </button>
    <button
      type="button"
      onClick={() => void exportAsPdf(title, columns, rows)}
      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-red-300 bg-red-50 text-red-800 hover:bg-red-100"
    >
      <Download className="w-4 h-4" /> PDF
    </button>
    <button
      type="button"
      onClick={() => window.print()}
      aria-label="Imprimir"
      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-blue-200 bg-blue-50 text-blue-800 hover:bg-blue-100"
    >
      <Printer className="w-4 h-4" />
    </button>
  </div>
);

export const EmptyState: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => (
  <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
    <p className="text-sm font-semibold text-slate-800">{title}</p>
    <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
  </div>
);

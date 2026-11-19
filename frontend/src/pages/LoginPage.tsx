import React, { useState } from "react";
import { KeyRound, Leaf } from "lucide-react";
import { apiClient } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Modal } from "../components/UiPrimitives";

export const LoginPage: React.FC = () => {
  const { login, offlineGraceExpired } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [resetOpen, setResetOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetMsg, setResetMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(identifier.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible iniciar sesión.");
    } finally {
      setBusy(false);
    }
  };

  const requestReset = async () => {
    setResetMsg("");
    try {
      const r = await apiClient.request<{ message: string; recovery_token?: string }>(
        "/api/v1/auth/password-reset/request",
        { method: "POST", body: JSON.stringify({ email: resetEmail }) }
      );
      if (r.recovery_token) setResetToken(r.recovery_token);
      setResetMsg(r.message);
    } catch (err) {
      setResetMsg(err instanceof Error ? err.message : "Error solicitando token.");
    }
  };

  const confirmReset = async () => {
    setResetMsg("");
    try {
      const r = await apiClient.request<{ message: string }>(
        "/api/v1/auth/password-reset/confirm",
        { method: "POST", body: JSON.stringify({ token: resetToken, new_password: newPassword }) }
      );
      setResetMsg(r.message);
    } catch (err) {
      setResetMsg(err instanceof Error ? err.message : "Error actualizando contraseña.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl overflow-hidden border border-slate-200">
        <div className="bg-brand-800 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-white text-leaf-700 flex items-center justify-center shadow">
              <Leaf className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-tight">SAJONA ADE</h1>
              <p className="text-xs text-red-100">Núcleo PWA • Módulos 1–3 + Dashboard</p>
            </div>
          </div>
          <span className="text-[11px] font-bold bg-brand-900 px-2.5 py-1 rounded-lg">
            TRL-6
          </span>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {offlineGraceExpired && (
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-3 text-xs text-amber-900">
              Tu sesión offline superó la ventana de gracia; conéctate para renovar credenciales.
            </div>
          )}
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-xs font-semibold text-red-800">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="login-id" className="block text-xs font-bold text-slate-700 mb-1">
              Usuario o Correo <span className="text-red-700">*</span>
            </label>
            <input
              id="login-id"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="ej. jefe o operario@sajona.co"
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:border-brand-700 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="login-pw" className="block text-xs font-bold text-slate-700 mb-1">
              Contraseña <span className="text-red-700">*</span>
            </label>
            <input
              id="login-pw"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:border-brand-700 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-leaf-700 hover:bg-leaf-600 text-white font-bold py-3 text-sm shadow transition disabled:opacity-50"
          >
            {busy ? "Ingresando..." : "Ingresar"}
          </button>

          <button
            type="button"
            onClick={() => setResetOpen(true)}
            className="w-full text-center text-xs font-semibold text-brand-800 hover:underline py-1"
          >
            ¿Olvidó la contraseña?
          </button>

          <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-[11px] text-slate-700 space-y-1">
            <div className="font-bold text-slate-900">Accesos de demostración (SAJONA Núcleo):</div>
            <div>
              <strong>Admin:</strong> admin / SajonaAdmin2026! • <strong>Jefe:</strong> jefe /
              SajonaJefe2026!
            </div>
            <div>
              <strong>Operario:</strong> operario / SajonaCampo2026! • <strong>Consulta:</strong>{" "}
              consulta / SajonaAudit2026!
            </div>
          </div>
        </form>
      </div>

      <Modal
        open={resetOpen}
        onClose={() => setResetOpen(false)}
        title="Recuperación de Contraseña"
        subtitle="Solicita un token temporal y confirma tu nueva contraseña"
      >
        <div className="space-y-3 text-xs">
          {resetMsg && (
            <div className="rounded-lg bg-slate-100 border border-slate-300 p-2.5 font-semibold text-slate-800">
              {resetMsg}
            </div>
          )}
          <div>
            <label className="block font-bold mb-1">Correo institucional / usuario</label>
            <div className="flex gap-2">
              <input
                type="email"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                placeholder="operario@sajona.co"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
              />
              <button
                type="button"
                onClick={() => void requestReset()}
                className="px-3 py-2 rounded-lg bg-slate-900 text-white font-semibold"
              >
                Generar token
              </button>
            </div>
          </div>
          <div>
            <label className="block font-bold mb-1">Token de recuperación</label>
            <input
              value={resetToken}
              onChange={(e) => setResetToken(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          <div>
            <label className="block font-bold mb-1">Nueva contraseña (mín. 8 caracteres)</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
          <button
            type="button"
            onClick={() => void confirmReset()}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-leaf-700 text-white font-bold"
          >
            <KeyRound className="w-4 h-4" /> Confirmar restablecimiento
          </button>
        </div>
      </Modal>
    </div>
  );
};

# ADR-005: Sesión Híbrida Online/Offline Segura, RBAC y Auditoría Append-Only

## Decisión
Autenticación con **Argon2id**, JWT Bearer de corta duración (`15 min`) y Refresh Token opaco rotatorio de un solo uso en cookie `HttpOnly; SameSite=Lax; Secure`, renovado mediante mutex único en cliente. Sin conexión se preserva únicamente perfil público, permisos RBAC y ventana de gracia temporal (`offline_grace_until`), excluyendo cualquier contraseña o hash en IndexedDB.

## Justificación
Cumple OWASP ASVS evitando robo de sesión por XSS y permite reapertura autónoma de la PWA en campo sin red.

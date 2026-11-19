# ADR-004: Despliegue Aislado en Contenedores Docker y Túnel HTTPS TLS 1.3

## Decisión
Desplegar cinco servicios aislados (`sajona-core-db`, `sajona-core-backend`, `sajona-core-backup`, `sajona-core-proxy` no-root en `127.0.0.1:8089:8080`, y `sajona-core-tunnel` Cloudflare) con `sajona-core-backend-net` configurada como `internal: true`.

## Justificación
Los Service Workers e instalación PWA exigen origen seguro HTTPS; el túnel saliente TLS 1.3 provee HTTPS inmediato sin alterar reglas de firewall del host ni interferir con otros servicios desplegados en la VPS.

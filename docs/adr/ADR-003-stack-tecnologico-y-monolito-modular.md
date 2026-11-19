# ADR-003: Stack Monolito Modular en 4 Capas y Desacople Estricto

## Decisión
Backend en **Python 3.12 + FastAPI + SQLAlchemy 2 Async + PostgreSQL 16.6** dividido en 4 capas (`domain`, `application`, `infrastructure`, `presentation`) verificadas automáticamente con `import-linter`, `mypy --strict` y `ruff`. Frontend en **React 18 + TypeScript estricto + Tailwind CSS + Dexie 4**, manteniendo las reglas puras agronómicas espejadas en TypeScript (`calculations.ts` y `dashboardStats.ts`).

## Justificación
Maximiza velocidad de respuesta (`p95 < 10 ms`), elimina la latencia de red entre microservicios dentro de la VPS y garantiza cero dependencias de framework en la lógica agronómica del dominio.

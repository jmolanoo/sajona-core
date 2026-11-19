from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sajona_core.config import get_settings
from sajona_core.infrastructure.database import get_db_session
from sajona_core.infrastructure.models import Base
from sajona_core.infrastructure.seed import run_seed_if_empty
from sajona_core.main import create_app


@pytest.fixture
async def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    db_file = tmp_path / "test_admin_edges.db"
    monkeypatch.setenv("AUDIT_LOG_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    get_settings.cache_clear()

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as s:
        await run_seed_if_empty(s)

    app = create_app()

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()
    get_settings.cache_clear()


async def _login(ac: AsyncClient, identifier: str, password: str) -> str:
    res = await ac.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert res.status_code == 200
    return str(res.json()["access_token"])


@pytest.mark.asyncio
async def test_admin_usuarios_logout_me_y_errores(client: AsyncClient) -> None:
    tok = await _login(client, "admin", "SajonaAdmin2026!")
    headers = {"Authorization": f"Bearer {tok}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "ADMIN"

    # Crear usuario nuevo + listar + actualizar
    created = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "nuevo_op",
            "email": "nuevo_op@sajona.co",
            "password": "ClaveTemporal2026!",
            "role": "OPERARIO",
            "nombre": "Andrés",
            "apellido": "Castro",
            "documento": "1075222333",
            "cargo": "Auxiliar Campo",
        },
    )
    assert created.status_code == 201
    uid = created.json()["id"]

    users = (await client.get("/api/v1/admin/users", headers=headers)).json()
    assert any(u["username"] == "nuevo_op" for u in users)

    upd = await client.patch(
        f"/api/v1/admin/users/{uid}",
        headers=headers,
        json={"role": "CONSULTA", "is_active": False},
    )
    assert upd.status_code == 200
    assert upd.json()["is_active"] is False

    # Intento de login de usuario inactivo -> 401
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "nuevo_op", "password": "ClaveTemporal2026!"},
    )
    assert bad_login.status_code == 401

    # Logout revoca cookie
    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_soft_delete_recalculo_unidad_descartada_y_sync_rechazos(client: AsyncClient) -> None:
    tok = await _login(client, "jefe", "SajonaJefe2026!")
    headers = {"Authorization": f"Bearer {tok}"}

    # Soft delete del trasplante de lote 031 revierte el estado del lote a SIEMBRA
    lote_31_id = "00000000-0000-4000-8000-000000000502"
    tp_31_id = "00000000-0000-4000-8000-000000000602"
    del_tp = await client.delete(f"/api/v1/entities/transplante_bolsa/{tp_31_id}", headers=headers)
    assert del_tp.status_code == 200

    props = (await client.get("/api/v1/entities/propagacion", headers=headers)).json()
    l31 = next(p for p in props if p["id"] == lote_31_id)
    assert l31["estado_lote"] == "SIEMBRA"

    # Marcar unidad madre #15 como DESCARTADA actualiza cantidad_madres_activas y bloquea extracción
    u15_id = "00000000-0000-4000-8000-000000000751"
    units = (
        await client.get(
            "/api/v1/entities/unidades_planta_madre?lote_madre_id=00000000-0000-4000-8000-000000000701",
            headers=headers,
        )
    ).json()
    u15 = next(u for u in units if u["id"] == u15_id)
    upd_u = await client.put(
        f"/api/v1/entities/unidades_planta_madre/{u15_id}",
        headers=headers,
        json={**u15, "estado_planta": "DESCARTADA"},
    )
    assert upd_u.status_code == 200

    ext_bad = await client.post(
        "/api/v1/entities/extracciones_madre",
        headers=headers,
        json={
            "lote_madre_id": "00000000-0000-4000-8000-000000000701",
            "fecha_transplante_ref": "2026-09-02",
            "fecha_extraccion": "2026-10-20",
            "detalle_plantas": [
                {"unidad_id": u15_id, "numero_planta": 15, "esquejes": 5, "semillas": 0}
            ],
        },
    )
    assert ext_bad.status_code == 422

    # Filtros de Dashboard
    dash = await client.get(
        "/api/v1/dashboard/summary"
        "?fecha_inicio=2026-08-01&fecha_fin=2026-12-31"
        "&variedad_id=00000000-0000-4000-8000-000000000301",
        headers=headers,
    )
    assert dash.status_code == 200
    assert dash.json()["kpi_propagacion"]["total_lotes"] == 2

    # Sync push con error de regla -> rejected + DELETE en sync
    bad_sync = await client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "mutations": [
                {
                    "client_mutation_id": f"mut-bad-{uuid4()}",
                    "entity_type": "propagacion",
                    "entity_id": str(uuid4()),
                    "operation": "CREATE",
                    "base_version": 0,
                    "payload": {
                        "codigo_lote": "BAD-SYNC",
                        "fecha_siembra": "2026-11-01",
                        "variedad_id": "00000000-0000-4000-8000-000000000301",
                        "tipo_incorporacion": "COMPRADA",
                        "proveedor": "",
                        "cantidad_material": 20,
                    },
                },
                {
                    "client_mutation_id": f"mut-del-{uuid4()}",
                    "entity_type": "variedades",
                    "entity_id": "00000000-0000-4000-8000-000000000303",
                    "operation": "DELETE",
                    "base_version": 1,
                    "payload": {},
                },
            ]
        },
    )
    assert bad_sync.status_code == 200
    res_list = bad_sync.json()["results"]
    assert res_list[0]["status"] == "rejected"
    # JEFE_PROYECTO no tiene permiso delete sobre variedades
    assert res_list[1]["status"] == "rejected"


@pytest.mark.asyncio
async def test_actualizaciones_404_409_y_pull_incremental(client: AsyncClient) -> None:
    tok = await _login(client, "admin", "SajonaAdmin2026!")
    headers = {"Authorization": f"Bearer {tok}"}

    # Tipo inválido y entidad inexistente -> 404 uniforme con correlation_id
    r404_type = await client.get("/api/v1/entities/inexistente", headers=headers)
    assert r404_type.status_code == 404
    assert "correlation_id" in r404_type.json()["error"]

    r404_item = await client.get("/api/v1/lotes/no-existe-id/trazabilidad", headers=headers)
    assert r404_item.status_code == 404

    # Actualizar propagación y provocar 409 Conflict con If-Match-Version obsoleta
    props = (await client.get("/api/v1/entities/propagacion", headers=headers)).json()
    l32 = next(p for p in props if p["codigo_lote"] == "LOT-2026-032")
    upd = await client.put(
        f"/api/v1/entities/propagacion/{l32['id']}",
        headers={**headers, "If-Match-Version": str(l32["version"])},
        json={**l32, "bajas_propagacion": 5, "observaciones": "Ajuste revisión"},
    )
    assert upd.status_code == 200
    assert upd.json()["version"] == 2

    conf = await client.put(
        f"/api/v1/entities/propagacion/{l32['id']}",
        headers={**headers, "If-Match-Version": "1"},
        json={**l32, "observaciones": "Versión vieja"},
    )
    assert conf.status_code == 409

    # Pull incremental con parámetro since y filtros de entidad
    pull = await client.get("/api/v1/sync/pull?since=2026-01-01T00:00:00Z", headers=headers)
    assert pull.status_code == 200
    assert len(pull.json()["changes"]["propagacion"]) >= 1

    # Soft delete en cadena offline sync (CREATE -> DELETE) y eliminar catálogo como ADMIN
    cid = str(uuid4())
    sync_del = await client.post(
        "/api/v1/sync/push",
        headers=headers,
        json={
            "mutations": [
                {
                    "client_mutation_id": f"m-c-{cid}",
                    "entity_type": "variedades",
                    "entity_id": cid,
                    "operation": "CREATE",
                    "base_version": 0,
                    "payload": {"nombre": "Temp Strain"},
                },
                {
                    "client_mutation_id": f"m-d-{cid}",
                    "entity_type": "variedades",
                    "entity_id": cid,
                    "operation": "DELETE",
                    "base_version": 1,
                    "payload": {},
                },
            ]
        },
    )
    assert sync_del.status_code == 200
    assert [r["status"] for r in sync_del.json()["results"]] == ["applied", "applied"]

    # Login fallido y reset de clave para correo inexistente
    assert (
        await client.post(
            "/api/v1/auth/login", json={"identifier": "admin", "password": "wrong"}
        )
    ).status_code == 401
    ghost = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": "noexiste@sajona.co"}
    )
    assert ghost.status_code == 200

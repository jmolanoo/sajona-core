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
    db_file = tmp_path / "test_sajona_core.db"
    audit_dir = tmp_path / "audit"
    monkeypatch.setenv("AUDIT_LOG_DIR", str(audit_dir))
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
async def test_health_y_openapi_contratos(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    openapi = await client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    for req_path in (
        "/api/v1/dashboard/summary",
        "/api/v1/sync/push",
        "/api/v1/sync/pull",
        "/api/v1/lotes/{lote_id}/trazabilidad",
    ):
        assert req_path in paths


@pytest.mark.asyncio
async def test_auth_rotacion_refresh_reset_y_rbac(client: AsyncClient) -> None:
    tok_oper = await _login(client, "operario", "SajonaCampo2026!")
    h_oper = {"Authorization": f"Bearer {tok_oper}"}
    # Operario no puede administrar usuarios ni auditoría
    assert (await client.get("/api/v1/admin/users", headers=h_oper)).status_code == 403
    assert (await client.get("/api/v1/admin/audit-logs", headers=h_oper)).status_code == 403

    # Refresh token rotation y detección de reuso
    tok_cons = await _login(client, "consulta", "SajonaAudit2026!")
    assert (
        await client.post(
            "/api/v1/entities/propagacion",
            headers={"Authorization": f"Bearer {tok_cons}"},
            json={
                "codigo_lote": "NOPE",
                "fecha_siembra": "2026-10-01",
                "variedad_id": "x",
                "cantidad_material": 10,
            },
        )
    ).status_code == 403

    old_cookie = client.cookies.get("sajona_core_refresh")
    assert old_cookie
    r_ref = await client.post("/api/v1/auth/refresh")
    assert r_ref.status_code == 200
    # Reuso del token revocado -> 401
    client.cookies.set("sajona_core_refresh", old_cookie)
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401

    # Password reset flow
    req = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "operario@sajona.co"},
    )
    assert req.status_code == 200
    rtok = req.json()["recovery_token"]
    conf = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": rtok, "new_password": "NuevaClaveSegura2026!"},
    )
    assert conf.status_code == 200
    await _login(client, "operario", "NuevaClaveSegura2026!")


@pytest.mark.asyncio
async def test_ciclo_integral_3_modulos_y_dashboard(client: AsyncClient) -> None:
    tok = await _login(client, "jefe", "SajonaJefe2026!")
    headers = {"Authorization": f"Bearer {tok}"}

    # 1. Crear lote Propagación y validar regla COMPRADA sin proveedor -> 422
    bad_prop = await client.post(
        "/api/v1/entities/propagacion",
        headers=headers,
        json={
            "codigo_lote": "LOT-TEST-BAD",
            "fecha_siembra": "2026-10-01",
            "variedad_id": "00000000-0000-4000-8000-000000000301",
            "tipo_propagacion": "SEMILLA",
            "tipo_incorporacion": "COMPRADA",
            "proveedor": "",
            "cantidad_material": 60,
        },
    )
    assert bad_prop.status_code == 422
    assert bad_prop.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"

    prop_resp = await client.post(
        "/api/v1/entities/propagacion",
        headers=headers,
        json={
            "codigo_lote": "LOT-2026-099",
            "fecha_siembra": "2026-10-01",
            "variedad_id": "00000000-0000-4000-8000-000000000301",
            "ubicacion_id": "00000000-0000-4000-8000-000000000401",
            "tipo_propagacion": "ESQUEJE",
            "tipo_incorporacion": "PROPIA",
            "cantidad_material": 50,
            "cantidad_plantas_madre": 10,
            "bajas_propagacion": 0,
        },
    )
    assert prop_resp.status_code == 201
    lote_id = prop_resp.json()["id"]

    # 2. Transplante a Bolsa promoviendo a Planta Madre (50 -> 45 buenas, 5 malas -> 10% merma)
    tp_resp = await client.post(
        "/api/v1/entities/transplante_bolsa",
        headers=headers,
        json={
            "lote_id": lote_id,
            "fecha_transplante": "2026-10-15",
            "ubicacion_id": "00000000-0000-4000-8000-000000000402",
            "cantidad_procesada": 50,
            "cantidad_buenas": 45,
            "tipo_lote": "PLANTA_MADRE",
            "promover_planta_madre": True,
        },
    )
    assert tp_resp.status_code == 201
    tp = tp_resp.json()
    assert tp["cantidad_malas"] == 5
    assert tp["porcentaje_buenas"] == 90.0
    assert tp["alerta_merma"] is False

    # Verificar que Propagación pasó a FINALIZADO y se creó LotePlantaMadre + Unidades
    props_all = (await client.get("/api/v1/entities/propagacion", headers=headers)).json()
    lote_upd = next(p for p in props_all if p["id"] == lote_id)
    assert lote_upd["estado_lote"] == "FINALIZADO"

    lm_list = (
        await client.get(f"/api/v1/entities/lotes_planta_madre?lote_id={lote_id}", headers=headers)
    ).json()
    assert len(lm_list) == 1
    lm_id = lm_list[0]["id"]
    unidades = (
        await client.get(
            f"/api/v1/entities/unidades_planta_madre?lote_madre_id={lm_id}", headers=headers
        )
    ).json()
    assert len(unidades) == 20

    # 3. Revisión Periódica en Bolsa (CV-05) + Extracción Madre (CV-09) con derivación de lote hijo
    rev_resp = await client.post(
        "/api/v1/entities/revisiones_bolsa",
        headers=headers,
        json={
            "transplante_id": tp["id"],
            "fecha_revision": "2026-10-20",
            "fase": "ENRAIZAMIENTO",
            "unidades_revisadas": 45,
            "contador_buenos": 43,
            "contador_malos": 2,
            "tipo_complicacion": "Estrés hídrico",
            "estado_sanitario": "OBSERVACION",
        },
    )
    assert rev_resp.status_code == 201

    ext_resp = await client.post(
        "/api/v1/entities/extracciones_madre",
        headers=headers,
        json={
            "lote_madre_id": lm_id,
            "fecha_transplante_ref": "2026-10-15",
            "fecha_extraccion": "2026-11-05",
            "detalle_plantas": [
                {
                    "unidad_id": unidades[0]["id"],
                    "numero_planta": unidades[0]["numero_planta"],
                    "esquejes": 12,
                    "semillas": 0,
                },
                {
                    "unidad_id": unidades[1]["id"],
                    "numero_planta": unidades[1]["numero_planta"],
                    "esquejes": 0,
                    "semillas": 8,
                },
            ],
            "lote_hijo_codigo": "LOT-2026-100",
        },
    )
    assert ext_resp.status_code == 201
    assert ext_resp.json()["total_esquejes"] == 12
    assert ext_resp.json()["total_semillas"] == 8

    # 4. Dashboard y Trazabilidad 360° reflejan toda la cadena
    trace = (await client.get(f"/api/v1/lotes/{lote_id}/trazabilidad", headers=headers)).json()
    assert trace["resumen"]["bajas_en_revisiones"] == 2
    assert trace["resumen"]["vivas_en_bolsa"] == 43
    assert trace["resumen"]["lotes_hijos_derivados"] == 1

    dash = (await client.get("/api/v1/dashboard/summary", headers=headers)).json()
    assert dash["kpi_propagacion"]["total_lotes"] >= 5
    assert dash["kpi_planta_madre"]["lotes_hijos_derivados"] >= 2


@pytest.mark.asyncio
async def test_offline_sync_idempotencia_y_conflictos(client: AsyncClient) -> None:
    tok = await _login(client, "operario", "SajonaCampo2026!")
    headers = {"Authorization": f"Bearer {tok}"}

    lote_id = str(uuid4())
    mut_id = f"mut-{uuid4()}"
    mut_create = {
        "mutations": [
            {
                "client_mutation_id": mut_id,
                "entity_type": "propagacion",
                "entity_id": lote_id,
                "operation": "CREATE",
                "base_version": 0,
                "payload": {
                    "codigo_lote": "LOT-OFFLINE-01",
                    "fecha_siembra": "2026-11-01",
                    "variedad_id": "00000000-0000-4000-8000-000000000301",
                    "tipo_propagacion": "ESQUEJE",
                    "tipo_incorporacion": "PROPIA",
                    "cantidad_material": 40,
                },
            }
        ]
    }
    p1 = await client.post("/api/v1/sync/push", headers=headers, json=mut_create)
    assert p1.status_code == 200
    assert p1.json()["results"][0]["status"] == "applied"

    # Reintento idempotente -> duplicate
    p_dup = await client.post("/api/v1/sync/push", headers=headers, json=mut_create)
    assert p_dup.json()["results"][0]["status"] == "duplicate"

    # Dispositivo B actualiza online -> version=2
    srv_lote = p1.json()["results"][0]["record"]
    upd_b = await client.put(
        f"/api/v1/entities/propagacion/{lote_id}",
        headers=headers,
        json={**srv_lote, "cantidad_material": 55},
    )
    assert upd_b.status_code == 200
    assert upd_b.json()["version"] == 2

    # Dispositivo A envía UPDATE offline basado en base_version=1 -> conflict
    mut_conflict = {
        "mutations": [
            {
                "client_mutation_id": f"mut-{uuid4()}",
                "entity_type": "propagacion",
                "entity_id": lote_id,
                "operation": "UPDATE",
                "base_version": 1,
                "payload": {**srv_lote, "cantidad_material": 45},
            }
        ]
    }
    p_conf = await client.post("/api/v1/sync/push", headers=headers, json=mut_conflict)
    assert p_conf.json()["results"][0]["status"] == "conflict"
    assert p_conf.json()["results"][0]["server_record"]["version"] == 2

    # Pull devuelve cambios + Admin ve bitácora completa
    pull = await client.get("/api/v1/sync/pull", headers=headers)
    assert pull.status_code == 200
    assert "propagacion" in pull.json()["changes"]

    tok_adm = await _login(client, "admin", "SajonaAdmin2026!")
    logs = await client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {tok_adm}"},
    )
    assert logs.status_code == 200
    assert len(logs.json()) >= 4

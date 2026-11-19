from sajona_core.domain.enums import RoleName
from sajona_core.domain.exceptions import AuthorizationError

ENTITY_PERMISSIONS: dict[str, dict[RoleName, set[str]]] = {
    "variedades": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write"},
        RoleName.OPERARIO: {"read"},
        RoleName.CONSULTA: {"read"},
    },
    "ubicaciones": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write"},
        RoleName.OPERARIO: {"read"},
        RoleName.CONSULTA: {"read"},
    },
    "funcionarios": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write"},
        RoleName.OPERARIO: {"read"},
        RoleName.CONSULTA: {"read"},
    },
    "propagacion": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
    "transplante_bolsa": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
    "revisiones_bolsa": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
    "lotes_planta_madre": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
    "unidades_planta_madre": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
    "extracciones_madre": {
        RoleName.ADMIN: {"read", "write", "delete"},
        RoleName.JEFE_PROYECTO: {"read", "write", "delete"},
        RoleName.OPERARIO: {"read", "write"},
        RoleName.CONSULTA: {"read"},
    },
}


def require_permission(role: RoleName, entity_type: str, action: str) -> None:
    allowed = ENTITY_PERMISSIONS.get(entity_type, {}).get(role, set())
    if action not in allowed:
        raise AuthorizationError(
            f"El rol '{role.value}' no tiene permiso '{action}' sobre '{entity_type}'."
        )


def require_admin(role: RoleName) -> None:
    if role != RoleName.ADMIN:
        raise AuthorizationError("Solo el rol ADMIN puede acceder a esta operación.")

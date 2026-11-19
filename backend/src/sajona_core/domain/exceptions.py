class DomainError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BusinessRuleViolationError(DomainError):
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION") -> None:
        super().__init__(code=code, message=message)


class EntityNotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: str) -> None:
        super().__init__(
            code="ENTITY_NOT_FOUND",
            message=f"{entity} con identificador '{entity_id}' no existe.",
        )


class ConflictError(DomainError):
    def __init__(self, message: str = "Conflicto de versión optimista.") -> None:
        super().__init__(code="VERSION_CONFLICT", message=message)


class AuthenticationError(DomainError):
    def __init__(self, message: str = "Credenciales inválidas.") -> None:
        super().__init__(code="AUTHENTICATION_FAILED", message=message)


class AuthorizationError(DomainError):
    def __init__(self, message: str = "No tiene permisos para ejecutar esta acción.") -> None:
        super().__init__(code="FORBIDDEN", message=message)

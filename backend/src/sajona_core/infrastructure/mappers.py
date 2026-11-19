from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.inspection import inspect


def _serialize_val(val: Any) -> Any:
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


def model_to_dict(obj: Any) -> dict[str, Any]:
    mapper = inspect(obj).mapper
    return {
        col.key: _serialize_val(getattr(obj, col.key))
        for col in mapper.column_attrs
    }

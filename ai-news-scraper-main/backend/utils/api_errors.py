"""Structured API error helpers for consistent fail-fast responses."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException


@dataclass(frozen=True)
class ApiErrorPayload:
    error_code: str
    error_message: str
    suggested_fix: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if payload["details"] is None:
            payload.pop("details")
        return payload


def structured_http_exception(
    status_code: int,
    error_code: str,
    error_message: str,
    suggested_fix: str,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ApiErrorPayload(
            error_code=error_code,
            error_message=error_message,
            suggested_fix=suggested_fix,
            details=details,
        ).to_dict(),
    )


def require_callable(obj: Any, method_name: str, error_code: str, suggested_fix: str):
    method = getattr(obj, method_name, None)
    if not callable(method):
        raise structured_http_exception(
            500,
            error_code,
            f"{obj.__class__.__name__}.{method_name} is not implemented",
            suggested_fix,
        )
    return method
from __future__ import annotations

from functools import wraps
from typing import Callable, Iterable, TypeVar

from flask import current_app, jsonify, request
from flask_login import current_user

F = TypeVar("F", bound=Callable[..., object])


def _login_disabled() -> bool:
    return bool(current_app.config.get("LOGIN_DISABLED"))


def require_roles(*roles: int) -> Callable[[F], F]:
    allowed: set[int] = set(int(r) for r in roles)

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if _login_disabled():
                return fn(*args, **kwargs)
            if not current_user.is_authenticated:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            if allowed and int(getattr(current_user, "role_id", -1)) not in allowed:
                return jsonify({"success": False, "error": "Access denied"}), 403
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def require_same_user_id(
    *,
    param: str,
    user_attr: str,
    sources: Iterable[str] = ("args", "json"),
) -> Callable[[F], F]:
    """
    Enforces that request param (from query args / json) matches current_user.<user_attr>.
    If param is missing, does nothing (caller may infer from current_user).
    """

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if _login_disabled():
                return fn(*args, **kwargs)
            if not current_user.is_authenticated:
                return jsonify({"success": False, "error": "Authentication required"}), 401

            requested = None
            if "args" in sources:
                requested = request.args.get(param)
            if requested is None and "json" in sources:
                body = request.get_json(silent=True) or {}
                requested = body.get(param)

            if requested is None:
                return fn(*args, **kwargs)

            expected = getattr(current_user, user_attr, None)
            if expected is None or str(requested) != str(expected):
                return jsonify({"success": False, "error": "Access denied"}), 403
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


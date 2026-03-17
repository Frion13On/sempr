import bcrypt
import re

_PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[^A-Za-z0-9]).{8,}$"
)


def is_strong_password(password: str) -> tuple[bool, str | None]:
    """
    Проверяет сложность пароля:
    - не короче 8 символов
    - содержит строчные и заглавные буквы
    - содержит хотя бы один специальный символ
    """
    if not password:
        return False, "Пароль не может быть пустым"
    if not _PASSWORD_COMPLEXITY_RE.match(password):
        return (
            False,
            "Пароль должен быть не короче 8 символов и содержать строчные и заглавные буквы, а также специальный символ",
        )
    return True, None


def hash_password(password: str) -> str:
    ok, error = is_strong_password(password)
    if not ok:
        raise ValueError(error or "Некорректный пароль")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False

    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception:
            return False

    return password == password_hash


def is_password_hashed(password_hash: str) -> bool:
    return password_hash.startswith("$2b$") or password_hash.startswith("$2a$")

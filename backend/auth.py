import secrets

from fastapi import Header, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import settings

SESSION_COOKIE_NAME = "techkev_session"
_SALT = "techkev-appstore-session"

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=_SALT)


def verify_credentials(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(username, settings.ADMIN_USER)
    pass_ok = secrets.compare_digest(password, settings.ADMIN_PASSWORD)
    return user_ok and pass_ok


def create_session_token(username: str) -> str:
    return _serializer.dumps({"user": username})


def _read_session(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        data = _serializer.loads(token, max_age=settings.SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user")


def get_current_user(request: Request) -> str | None:
    """Liest den eingeloggten Benutzer aus dem Session-Cookie, ohne einen Fehler
    auszuloesen (z. B. fuer optionale Anzeige im Template)."""
    return _read_session(request)


def require_login(request: Request) -> str:
    """Dependency fuer geschuetzte Web-Interface-Routen. Leitet bei fehlender
    oder ungueltiger Session zur Login-Seite weiter."""
    user = _read_session(request)
    if not user:
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/login?next={request.url.path}"},
        )
    return user


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Dependency fuer die Android-API. Erwartet den Header 'X-API-Key'."""
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Ungueltiger oder fehlender API-Key")

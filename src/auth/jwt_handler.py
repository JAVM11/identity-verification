"""
Manejo de JWT simplificado para el demo.
En producción se valida contra auth_token_session en MySQL.
"""
import time
import uuid
import jwt
from src.config import JWT_SECRET, JWT_ALGORITHM, JWT_ISSUER, JWT_EXPIRES_SECONDS


def generar_token(claims_extra: dict) -> str:
    """Genera un access token JWT de demo."""
    issued_at = int(time.time())
    expires_at = issued_at + JWT_EXPIRES_SECONDS
    jti = str(uuid.uuid4())

    claims = {
        "iss": JWT_ISSUER,
        "iat": issued_at,
        "exp": expires_at,
        "jti": jti,
    }
    claims.update(claims_extra)

    token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


def validar_token(token: str) -> tuple:
    """Valida firma, issuer y expiración."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER
        )
        return True, payload, None
    except jwt.ExpiredSignatureError:
        return False, None, "TOKEN_EXPIRED"
    except jwt.InvalidTokenError:
        return False, None, "INVALID_TOKEN"

"""
Configuración centralizada. 
En producción estos valores vienen de variables de entorno.
"""
import os

# ── Flask ──
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# ── JWT ──
JWT_ISSUER = os.getenv("JWT_ISSUER", "idve-demo-issuer")
JWT_SECRET = os.getenv("JWT_SECRET", "CAMBIAR_ESTE_SECRETO")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_SECONDS = int(os.getenv("JWT_EXPIRES_SECONDS", "3600"))

# ── MySQL (solo referencia, el demo usa mock) ──
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "idve_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "idve_db")
MYSQL_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", "5"))

# ── Paths ──
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads_demo")
LOG_FOLDER = os.getenv("LOG_FOLDER", "logs")

# ── Auth Environments ──
AUTH_ENVIRONMENTS_VALIDOS = {"sandbox", "production"}

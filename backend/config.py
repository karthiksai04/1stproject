"""
CartCompass-BI - Application Configuration
Reads environment variables with secure defaults for local and production deployment.
"""

import os
import secrets
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    DASHBOARD_USERNAME = os.environ.get("DASHBOARD_USERNAME") or ("admin" if DEBUG else None)
    DASHBOARD_PASSWORD_HASH = os.environ.get("DASHBOARD_PASSWORD_HASH") or (
        "scrypt:32768:8:1$9WDn1vTU3d33deVL$fffbcdc2edb6c61d7d8840ad7c31f470ca467c1245ec7532b93c14ab1d8afb1006bd3c97b68c2e6bb4b5aaac88c7125198b0e4a246ca2d1aa506e29f1e0b434d"
        if DEBUG else None
    )
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "cartcompass.db"))).resolve()
    DEFAULT_CURRENCY = os.environ.get("DEFAULT_CURRENCY", "₹")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "t")
    PORT = int(os.environ.get("PORT", 5000))
    HOST = os.environ.get("HOST", "127.0.0.1")
    FRONTEND_DIR = BASE_DIR / "frontend"
    CHART_OUTPUTS_DIR = BASE_DIR / "analysis" / "outputs"


class TestingConfig(Config):
    """Testing configuration with temporary database."""
    TESTING = True
    DEBUG = False
    DATABASE_PATH = BASE_DIR / "tests" / "test_cartcompass.db"

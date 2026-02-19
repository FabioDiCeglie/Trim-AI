from routes.health import health
from routes.openapi import docs, openapi_json
from routes.connect import connect

__all__ = ["health", "docs", "openapi_json", "connect"]

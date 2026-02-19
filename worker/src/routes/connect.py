"""
POST /api/v1/connect

1. Parse + validate { provider, credentials } from request body
2. Encrypt the credentials blob with AES-GCM
3. Store the encrypted blob in KV under a UUID connectionId
4. Return { connectionId, provider } to the frontend

The frontend stores connectionId in localStorage and sends it as
Authorization: Bearer <connectionId> on every subsequent request.
"""
import json
import js
from workers import Response
from services import CryptoService
from utils import error, ok


SUPPORTED_PROVIDERS = {"gcp", "aws", "azure", "k8s"}

REQUIRED_FIELDS: dict[str, list[str]] = {
    "gcp":   ["type", "project_id", "private_key", "client_email"],
    "aws":   ["access_key_id", "secret_access_key", "region"],
    "azure": ["tenant_id", "client_id", "client_secret"],
    "k8s":   ["kubeconfig"],
}


async def connect(env, request) -> Response:
    try:
        body = json.loads(await request.text())
    except Exception:
        return error("Invalid JSON body", 400)

    provider = str(body.get("provider", "")).lower()
    credentials = body.get("credentials")

    if provider not in SUPPORTED_PROVIDERS:
        return error(
            f"Unsupported provider '{provider}'. Must be one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}",
            400,
        )

    if not credentials or not isinstance(credentials, dict):
        return error("Missing or invalid 'credentials' object", 400)

    missing = [f for f in REQUIRED_FIELDS[provider] if not credentials.get(f)]
    if missing:
        return error(f"Missing credential fields: {', '.join(missing)}", 400)

    crypto = CryptoService(env.ENCRYPTION_KEY)
    payload = json.dumps({"provider": provider, "credentials": credentials})
    encrypted = await crypto.encrypt(payload)

    connection_id = str(js.crypto.randomUUID())
    await env.CREDENTIALS.put(
        connection_id,
        json.dumps(encrypted),
        expirationTtl=86400 * 30,
    )

    return ok({"connectionId": connection_id, "provider": provider}, status=201)

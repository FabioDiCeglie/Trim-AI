import json
from services.crypto_service import CryptoService


class CredentialService:
    """Resolves a connectionId from the Authorization header into decrypted provider credentials."""

    def __init__(self, env):
        """Initialize with the Cloudflare env (needs env.CREDENTIALS KV and env.ENCRYPTION_KEY)."""
        self._kv = env.CREDENTIALS
        self._crypto = CryptoService(env.ENCRYPTION_KEY)

    async def resolve(self, request) -> dict | None:
        """
        Extract the connectionId from the Authorization: Bearer header,
        look it up in KV, and decrypt the stored blob.

        Returns { provider, credentials } if found and valid, or None if
        the header is missing, the connectionId doesn't exist in KV, or
        decryption fails.
        """
        connection_id = self._extract_connection_id(request)
        if not connection_id:
            return None

        raw = await self._kv.get(connection_id)
        if not raw:
            return None

        try:
            encrypted = json.loads(raw)
            plaintext = await self._crypto.decrypt(encrypted)
            return json.loads(plaintext)
        except Exception:
            return None

    @staticmethod
    def _extract_connection_id(request) -> str | None:
        """Parse the connectionId out of Authorization: Bearer <connectionId>."""
        auth = request.headers.get("Authorization") or ""
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        return None

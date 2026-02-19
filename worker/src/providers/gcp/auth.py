import js
import json
import base64
import time
from pyodide.ffi import to_js


class GCPAuthService:
    """
    Obtains a short-lived GCP access token from a Service Account.

    GCP does not accept the private key directly — you must:
    1. Build a JWT signed with the Service Account's RSA private key
    2. POST it to Google's token endpoint
    3. Get back a bearer access token valid for 1 hour

    All signing is done via the Web Crypto API (js.crypto.subtle) so no
    native Python crypto libraries are needed.
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPE = "https://www.googleapis.com/auth/cloud-platform"

    def __init__(self, credentials: dict):
        """
        credentials: decrypted GCP Service Account dict
        (type, project_id, private_key, client_email)
        """
        self._client_email = credentials["client_email"]
        self._private_key_pem = credentials["private_key"]

    async def get_access_token(self) -> str:
        """
        Sign a JWT with the Service Account private key and exchange it
        for a GCP access token. Returns the bearer token string.
        """
        jwt = await self._build_jwt()
        return await self._exchange_jwt(jwt)

    async def _build_jwt(self) -> str:
        """
        Build and sign a JWT assertion:
          header.payload.signature  (all base64url-encoded)
        """
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": self._client_email,
            "sub": self._client_email,
            "aud": self.TOKEN_URL,
            "scope": self.SCOPE,
            "iat": now,
            "exp": now + 3600,
        }

        header_b64 = _b64url(json.dumps(header))
        payload_b64 = _b64url(json.dumps(payload))
        signing_input = f"{header_b64}.{payload_b64}"

        key = await self._import_private_key()
        signature = await self._sign(signing_input, key)

        return f"{signing_input}.{signature}"

    async def _import_private_key(self):
        """Import the PEM private key as a Web Crypto CryptoKey for RS256 signing."""
        pem_body = (
            self._private_key_pem
            .replace("-----BEGIN PRIVATE KEY-----", "")
            .replace("-----END PRIVATE KEY-----", "")
            .replace("-----BEGIN RSA PRIVATE KEY-----", "")
            .replace("-----END RSA PRIVATE KEY-----", "")
            .replace("\n", "")
            .strip()
        )
        der_bytes = list(base64.b64decode(pem_body))
        key_data = js.Uint8Array.new(to_js(der_bytes))

        return await js.crypto.subtle.importKey(
            "pkcs8",
            key_data,
            to_js({"name": "RSASSA-PKCS1-v1_5", "hash": "SHA-256"}, dict_converter=js.Object.fromEntries),
            False,
            to_js(["sign"]),
        )

    async def _sign(self, data: str, key) -> str:
        """Sign the JWT header.payload string and return a base64url-encoded signature."""
        data_bytes = to_js(list(data.encode("utf-8")))
        data_js = js.Uint8Array.new(data_bytes)

        sig_buffer = await js.crypto.subtle.sign(
            to_js({"name": "RSASSA-PKCS1-v1_5"}, dict_converter=js.Object.fromEntries),
            key,
            data_js,
        )
        sig_bytes = bytes(list(js.Uint8Array.new(sig_buffer)))
        return base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode()

    async def _exchange_jwt(self, jwt: str) -> str:
        """POST the signed JWT to Google's token endpoint and return the access token."""
        body = f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion={jwt}"
        resp = await js.fetch(
            self.TOKEN_URL,
            to_js({
                "method": "POST",
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                "body": body,
            }, dict_converter=js.Object.fromEntries),
        )
        data = json.loads(await resp.text())
        if "access_token" not in data:
            raise Exception(f"GCP token error: {data.get('error_description', data)}")
        return data["access_token"]


def _b64url(s: str) -> str:
    """Base64url-encode a string (no padding)."""
    return base64.urlsafe_b64encode(s.encode()).rstrip(b"=").decode()

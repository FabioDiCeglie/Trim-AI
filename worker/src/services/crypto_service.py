import js
import base64
from pyodide.ffi import to_js


class CryptoService:
    """AES-GCM encryption/decryption using the Web Crypto API (js.crypto.subtle)."""

    def __init__(self, encryption_key_b64: str):
        """Initialize with a base64-encoded 32-byte AES-GCM key (from env.ENCRYPTION_KEY)."""
        self._key_b64 = encryption_key_b64

    async def encrypt(self, plaintext: str) -> dict:
        """
        Encrypt a plaintext string using AES-GCM.

        AES-GCM is an authenticated encryption algorithm — it both encrypts the data
        AND produces an authentication tag, so any tampering with the ciphertext is detected.

        We generate a random 12-byte IV (Initialization Vector) for every encryption call.
        Using a fresh IV each time means that encrypting the same plaintext twice produces
        a completely different ciphertext — preventing pattern analysis attacks.

        Returns a dict with two base64-encoded strings:
          - iv:         the random IV needed to decrypt later (safe to store alongside ciphertext)
          - ciphertext: the encrypted + authenticated payload
        """
        key = await self._import_key()

        iv_bytes = list(js.crypto.getRandomValues(js.Uint8Array.new(12)))
        iv_js = js.Uint8Array.new(to_js(iv_bytes))
        data_js = js.Uint8Array.new(to_js(list(plaintext.encode("utf-8"))))

        cipher_buffer = await js.crypto.subtle.encrypt(
            self._obj({"name": "AES-GCM", "iv": iv_js}),
            key,
            data_js,
        )
        cipher_bytes = list(js.Uint8Array.new(cipher_buffer))

        return {
            "iv": base64.b64encode(bytes(iv_bytes)).decode(),
            "ciphertext": base64.b64encode(bytes(cipher_bytes)).decode(),
        }

    async def decrypt(self, encrypted: dict) -> str:
        """
        Decrypt an { iv, ciphertext } dict back to the original plaintext.

        We pass the same IV that was used during encryption — without it the
        decryption produces garbage. The IV is not a secret (it's stored next to
        the ciphertext in KV), but the ENCRYPTION_KEY is — and without the key,
        the ciphertext cannot be decrypted even if you have both the IV and the blob.

        AES-GCM also verifies the authentication tag during decryption and raises
        an error if the ciphertext was modified, so we get integrity checking for free.
        """
        key = await self._import_key()

        iv_js = js.Uint8Array.new(to_js(list(base64.b64decode(encrypted["iv"]))))
        cipher_js = js.Uint8Array.new(to_js(list(base64.b64decode(encrypted["ciphertext"]))))

        plain_buffer = await js.crypto.subtle.decrypt(
            self._obj({"name": "AES-GCM", "iv": iv_js}),
            key,
            cipher_js,
        )
        return bytes(list(js.Uint8Array.new(plain_buffer))).decode("utf-8")

    async def _import_key(self):
        """
        Convert the raw base64 key into a Web Crypto CryptoKey object.

        The Web Crypto API requires keys to be imported before use — it won't
        accept raw bytes directly. Setting extractable=False means the key
        material can never be read back out of the runtime after import.
        """
        raw = base64.b64decode(self._key_b64)
        key_data = js.Uint8Array.new(to_js(list(raw)))
        return await js.crypto.subtle.importKey(
            "raw",
            key_data,
            self._obj({"name": "AES-GCM"}),
            False,
            to_js(["encrypt", "decrypt"]),
        )

    @staticmethod
    def _obj(d: dict):
        """Convert a Python dict to a JS object for Web Crypto API calls."""
        return to_js(d, dict_converter=js.Object.fromEntries)

"""Symmetric encryption helpers for secrets at rest (user API keys).

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the ``cryptography`` package. The
key is derived from ``settings.ai_encryption_key`` so we never store a raw,
reusable secret in the source tree.

Design notes:
  * A single app-wide key encrypts every user's provider key. Rotating it
    requires re-encrypting stored values; acceptable for this app's scale.
  * If ``AI_ENCRYPTION_KEY`` is not a valid 32-byte urlsafe-base64 Fernet key,
    we deterministically derive one from it via SHA-256 so operators can set
    any sufficiently-strong passphrase.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _derive_fernet_key(raw: str) -> bytes:
    """Return a valid urlsafe-base64 32-byte Fernet key from any input string.

    If ``raw`` is already a valid Fernet key we use it directly; otherwise we
    hash it to 32 bytes and base64-encode — deterministic and stable across
    restarts so previously-encrypted values remain decryptable.
    """
    candidate = raw.strip().encode("utf-8")
    try:
        # Validate: a real Fernet key is 32 urlsafe-base64 bytes.
        if len(base64.urlsafe_b64decode(candidate)) == 32:
            return candidate
    except (ValueError, Exception):  # noqa: BLE001
        pass
    digest = hashlib.sha256(candidate).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_fernet_key(settings.ai_encryption_key))


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret, returning urlsafe-base64 ciphertext (str)."""
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt ciphertext produced by :func:`encrypt_secret`.

    Raises ``InvalidToken`` if the value was encrypted under a different key
    (e.g. the encryption key was rotated) or has been tampered with.
    """
    return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


__all__ = ["encrypt_secret", "decrypt_secret", "InvalidToken"]

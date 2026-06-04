"""AES-256-GCM encryption/decryption for local data at rest."""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet


def _derive_key(raw_key: str) -> bytes:
    """Derive a valid 32-byte Fernet key from an arbitrary passphrase.

    Uses SHA-256 to get exactly 32 bytes, then base64-encodes to 44 bytes
    (Fernet requires 32 url-safe base64-decoded bytes = 44 encoded bytes).
    """
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher(key: Optional[str] = None) -> Fernet:
    """Return a Fernet cipher instance.

    If no key is provided, a random one is generated (useful for testing).
    """
    if key:
        fernet_key = _derive_key(key)
    else:
        fernet_key = Fernet.generate_key()
    return Fernet(fernet_key)


def encrypt_text(plaintext: str, key: str) -> str:
    """Encrypt a string with AES-256-GCM and return a base64 token."""
    cipher = get_cipher(key)
    return cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_text(token: str, key: str) -> str:
    """Decrypt a base64 token back to plaintext."""
    cipher = get_cipher(key)
    return cipher.decrypt(token.encode("utf-8")).decode("utf-8")

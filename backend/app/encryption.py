"""
CodeLens AI - AES-256 Encryption Module
Sensitive data encryption at rest using AES-256-GCM.
"""
import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ─── Configuration ──────────────────────────────────────────────

def _get_encryption_key() -> bytes:
    """Get or derive the AES-256 encryption key from environment"""
    key_b64 = os.getenv("CODELENS_ENCRYPTION_KEY")
    if key_b64:
        key = base64.b64decode(key_b64)
        if len(key) == 32:
            return key
        # Derive 32-byte key from provided key
        return hashlib.sha256(key).digest()

    # Use secret if provided, otherwise derive from JWT_SECRET
    secret = os.getenv("JWT_SECRET", "default-dev-key")
    return hashlib.sha256(secret.encode()).digest()


_AESGCM = AESGCM(_get_encryption_key())


# ─── High-Level API ─────────────────────────────────────────────

def encrypt(plaintext: str) -> str:
    """
    Encrypt a string using AES-256-GCM.
    Returns base64-encoded string: nonce(12) + ciphertext + tag(16).
    """
    if not plaintext:
        return ""

    nonce = os.urandom(12)
    ciphertext = _AESGCM.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Format: base64(nonce || ciphertext)
    combined = nonce + ciphertext
    return base64.b64encode(combined).decode()


def decrypt(encrypted: str) -> str:
    """
    Decrypt an AES-256-GCM encrypted string.
    """
    if not encrypted:
        return ""

    try:
        combined = base64.b64decode(encrypted)
        nonce = combined[:12]
        ciphertext = combined[12:]
        plaintext = _AESGCM.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def encrypt_dict(data: dict, fields: list[str]) -> dict:
    """
    Encrypt specified fields in a dictionary.
    Returns a new dict with specified fields encrypted.
    """
    result = dict(data)
    for field in fields:
        if field in result and result[field]:
            result[field + "_encrypted"] = encrypt(str(result[field]))
            if field != result.get(field + "_encrypted", ""):
                del result[field]
    return result


def hash_sensitive(value: str) -> str:
    """
    One-way hash for sensitive values that need comparison but not retrieval.
    Uses SHA-256 with salt prefix.
    """
    salt = os.getenv("CODELENS_HASH_SALT", "codelens-v1")
    return hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()


# ─── Usage Markers ──────────────────────────────────────────────

# These are the fields we recommend encrypting:
RECOMMENDED_ENCRYPT_FIELDS = [
    "api_key",
    "secret",
    "private_key",
    "password",
    "token",
    "credit_card",
]

# For CodeLens AI SaaS, we encrypt:
# - Webhook secrets
# - SSO client secrets
# - Custom IdP certificates

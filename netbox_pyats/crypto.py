"""Encryption helpers for the plugin-local PyATS credential store.

Field-level encryption uses ``cryptography.fernet.Fernet`` (symmetric authenticated
encryption). The key is resolved once per process from, in priority order:

1. ``PLUGINS_CONFIG['netbox_pyats']['credential_key']`` — operator-provided key
   (recommended for production). Must be a 32-byte url-safe base64-encoded value
   (the result of ``Fernet.generate_key()``).
2. A deterministic slice of NetBox's ``SECRET_KEY`` — a *fallback for dev only*.
   We derive a Fernet key by hashing the first 64 chars of ``SECRET_KEY`` with
   SHA256 so a stable key is produced without the operator configuring anything.

The fallback exists so the plugin works out-of-the-box in a dev environment; we
emit a clear warning when it is used so operators do not ship it to production by
accident. Credentials encrypted with one key cannot be decrypted with another,
so rotating the key requires re-keying existing credential rows (out of scope
for v1; tracked as an operator runbook note).
"""

from __future__ import annotations

import base64
import hashlib
import warnings

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_config() -> dict:
    """Return the plugin's PLUGINS_CONFIG block (empty dict if unset)."""
    return getattr(settings, "PLUGINS_CONFIG", {}).get("netbox_pyats", {}) or {}


def _derive_fernet_key_from_secret_key(secret_key: str) -> bytes:
    """Derive a 32-byte url-safe base64 Fernet key from a slice of SECRET_KEY.

    SHA-256 over the first 64 chars (padded if shorter) gives a stable,
    deterministic 32-byte digest we base64-encode for Fernet. This is *not*
    cryptographically stronger than SECRET_KEY itself — the fallback exists so
    the plugin runs in dev without configuration. Operators should set
    ``credential_key`` for production.
    """
    material = (secret_key or "").ljust(64, "_")[:64]
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet_key() -> bytes:
    """Resolve the Fernet key for the current process.

    Priority:
      1. ``PLUGINS_CONFIG['netbox_pyats']['credential_key']`` (must be valid
         Fernet key material — a 32-byte url-safe base64 string).
      2. Derived from a slice of ``settings.SECRET_KEY`` (dev fallback, warns).
    """
    cfg = _get_config()
    configured = cfg.get("credential_key")
    if configured:
        try:
            key = configured.encode("utf-8") if isinstance(configured, str) else configured
            Fernet(key)  # validate format; raises ValueError on bad key
            return key
        except (ValueError, TypeError) as exc:
            raise ImproperlyConfigured(
                "netbox_pyats: PLUGINS_CONFIG['netbox_pyats']['credential_key'] is set but is not a "
                f'valid Fernet key. Generate one with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. '
                f"Underlying error: {exc}"
            ) from exc

    secret_key = getattr(settings, "SECRET_KEY", "") or ""
    if not secret_key:
        raise ImproperlyConfigured(
            "netbox_pyats: cannot derive a credential encryption key — neither "
            "PLUGINS_CONFIG['netbox_pyats']['credential_key'] nor Django SECRET_KEY is set."
        )
    warnings.warn(
        "netbox_pyats: no PLUGINS_CONFIG['netbox_pyats']['credential_key'] configured; falling back to a "
        "key derived from SECRET_KEY. This is acceptable for dev but MUST be replaced with a dedicated "
        "credential_key in production. Rotate by setting credential_key and re-keying existing credentials.",
        RuntimeWarning,
        stacklevel=2,
    )
    return _derive_fernet_key_from_secret_key(secret_key)


def encrypt(plaintext: str) -> str:
    """Encrypt a UTF-8 string and return a Fernet token as a utf-8 string.

    Empty/None inputs round-trip to an empty string so model fields can stay
    blank=True without the encryption helpers raising.
    """
    if not plaintext:
        return ""
    f = Fernet(get_fernet_key())
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt a Fernet token produced by :func:`encrypt`.

    Empty input round-trips to an empty string. A tampered or wrong-key token
    raises :class:`cryptography.fernet.InvalidToken`; callers should catch that
    to surface a friendly error rather than crash the model accessor.
    """
    if not token:
        return ""
    f = Fernet(get_fernet_key())
    return f.decrypt(token.encode("utf-8")).decode("utf-8")


def is_encrypted_token(value: str) -> bool:
    """Best-effort check that a stored value looks like a Fernet token.

    Used by tests to assert that values stored on the model are ciphertext
    and not the original secret. Fernet tokens are url-safe base64 strings
    starting with the version byte ``gAAAAA`` (version 0x80 + timestamp).
    We do not attempt a decrypt here so this check is safe to call with a
    key other than the one that produced the token.
    """
    if not value:
        return False
    return value.startswith("gAAAAA")

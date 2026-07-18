"""Field-level encryption for :mod:`netbox_pyats` secrets.

Secrets (``password``, ``enable_secret``) are encrypted at rest with
``cryptography.fernet.Fernet``. Two layers of indirection keep the secret key
out of the model code:

1. The Fernet key is resolved at call time from
   ``PLUGINS_CONFIG['netbox_pyats']['credential_key']`` when set.
2. When not set, and ``credential_key_fallback_to_secret_key`` is true (the
   default), a deterministic 32-byte key is derived from a stable slice of
   NetBox's ``SECRET_KEY``. This lets the plugin work out of the box; operators
   are encouraged to set a dedicated key for production deployments.

Encrypted values are stored prefixed with ``ENC1:`` so we can distinguish
already-encrypted values from plain text (defensive against double-encryption
and accidental plaintext writes), and so the helper round-trips cleanly.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

ENC_PREFIX = "ENC1:"


class EncryptionError(Exception):
    """Raised when encryption key configuration is invalid or decryption fails."""


def _settings_value(name: str, default=None):
    """Best-effort lookup of a PLUGINS_CONFIG value for this plugin.

    Keeps this module importable without Django settings configured (used in
    the pure-Python test suite, which calls :func:`configure_for_tests`).
    """
    try:
        from django.conf import settings  # local import keeps test surface small
    except ModuleNotFoundError:  # pragma: no cover - django is a hard dep of netbox
        return default
    plugins_config = getattr(settings, "PLUGINS_CONFIG", {}) or {}
    plugin_cfg = plugins_config.get("netbox_pyats", {}) or {}
    return plugin_cfg.get(name, default)


def _secret_key() -> str:
    """Return NetBox SECRET_KEY (or a stable placeholder in tests)."""
    try:
        from django.conf import settings

        return getattr(settings, "SECRET_KEY", "") or ""
    except ModuleNotFoundError:
        return ""


def _derive_fernet_key_from_secret_key(secret_key: str) -> bytes:
    """Derive a 32-byte url-safe Fernet key from a slice of SECRET_KEY.

    Fernet keys are 32 url-safe base64 bytes. We hash a stable slice of
    SECRET_KEY with SHA-256 (deterministic, not a KDF — SECRET_KEY is already a
    secret, not a password) and base64-encode the digest.
    """
    if not secret_key:
        raise EncryptionError(
            "No credential_key configured and NetBox SECRET_KEY is empty; "
            "cannot derive an encryption key. Set "
            "PLUGINS_CONFIG['netbox_pyats']['credential_key'] to a Fernet key."
        )
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def resolve_fernet() -> Fernet:
    """Build the :class:`Fernet` to use for credential encryption.

    Order of resolution:
    1. ``PLUGINS_CONFIG['netbox_pyats']['credential_key']`` (a Fernet key).
    2. If empty and ``credential_key_fallback_to_secret_key`` is true (default),
       derive from NetBox ``SECRET_KEY``.
    3. Otherwise raise :class:`EncryptionError`.
    """
    key = _settings_value("credential_key", "") or ""
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    key = key.strip()
    if key:
        try:
            return Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise EncryptionError(
                f"PLUGINS_CONFIG['netbox_pyats']['credential_key'] is not a valid " f"Fernet key: {exc}"
            ) from exc

    fallback = _settings_value("credential_key_fallback_to_secret_key", True)
    if not fallback:
        raise EncryptionError(
            "credential_key is not set and credential_key_fallback_to_secret_key "
            "is False; cannot resolve an encryption key."
        )
    return Fernet(_derive_fernet_key_from_secret_key(_secret_key()))


def encrypt(value: str) -> str:
    """Encrypt a plaintext secret, returning the ``ENC1:``-prefixed ciphertext."""
    if value is None:
        return ""
    if isinstance(value, str) and value.startswith(ENC_PREFIX):
        # Already encrypted; idempotent.
        return value
    f = resolve_fernet()
    token = f.encrypt(value.encode("utf-8")).decode("ascii")
    return f"{ENC_PREFIX}{token}"


def decrypt(value: str) -> str:
    """Decrypt an ``ENC1:``-prefixed ciphertext back to plaintext."""
    if not value:
        return ""
    if not isinstance(value, str) or not value.startswith(ENC_PREFIX):
        # Not encrypted (e.g. legacy plaintext). Return as-is so reads keep
        # working until the value is re-saved with encryption.
        return value
    f = resolve_fernet()
    token = value[len(ENC_PREFIX) :]
    try:
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise EncryptionError("Could not decrypt credential: invalid key or token.") from exc


def configure_for_tests(secret_key: str = "test-secret-key-for-pyats-plugin") -> None:
    """Configure Django settings so encryption works without NetBox installed.

    Used by the pure-Python test suite. Sets a minimal PLUGINS_CONFIG that uses
    a derived key (exercising the fallback path) so the production fallback
    code is covered by tests.
    """
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY=secret_key,
            PLUGINS_CONFIG={
                "netbox_pyats": {
                    "credential_key": "",
                    "credential_key_fallback_to_secret_key": True,
                }
            },
        )
        import django

        django.setup()
    elif not getattr(settings, "PLUGINS_CONFIG", None):
        settings.PLUGINS_CONFIG = {
            "netbox_pyats": {
                "credential_key": "",
                "credential_key_fallback_to_secret_key": True,
            }
        }

"""Unit tests for :mod:`netbox_pyats.crypto`.

These are pure-Python and run without NetBox installed (the minimal Django
settings configured by ``conftest.py`` supply SECRET_KEY and PLUGINS_CONFIG).
They cover the full encryption round-trip, key resolution paths, idempotency,
and the fallback-to-SECRET_KEY behavior that ships as the default.
"""

import base64
import hashlib

import pytest
from cryptography.fernet import Fernet

from netbox_pyats import crypto


def _set_config(credential_key="", fallback=True):
    from django.conf import settings

    settings.PLUGINS_CONFIG = {
        "netbox_pyats": {
            "credential_key": credential_key,
            "credential_key_fallback_to_secret_key": fallback,
        }
    }


def test_round_trip_encrypt_decrypt_with_dedicated_key():
    """Encrypt with a dedicated Fernet key and decrypt back to the plaintext."""
    key = base64.urlsafe_b64encode(b"0" * 32).decode("ascii")
    _set_config(credential_key=key)
    secret = "my-super-secret-password"
    enc = crypto.encrypt(secret)
    assert enc.startswith(crypto.ENC_PREFIX)
    assert enc != secret
    dec = crypto.decrypt(enc)
    assert dec == secret


def test_encrypt_is_idempotent():
    """Encrypting an already-encrypted value returns it unchanged."""
    key = base64.urlsafe_b64encode(b"0" * 32).decode("ascii")
    _set_config(credential_key=key)
    enc = crypto.encrypt("hello")
    assert crypto.encrypt(enc) == enc


def test_decrypt_empty_returns_empty():
    assert crypto.decrypt("") == ""
    assert crypto.decrypt(None) == ""  # type: ignore[arg-type]


def test_decrypt_unencrypted_passthrough():
    """A value without the ENC prefix is returned as-is (legacy plaintext)."""
    _set_config(credential_key="")
    assert crypto.decrypt("plain-text") == "plain-text"


def test_fallback_to_secret_key_when_no_credential_key():
    """When credential_key is empty, derive from SECRET_KEY (the default)."""
    from django.conf import settings

    _set_config(credential_key="", fallback=True)
    expected_key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest())
    f = crypto.resolve_fernet()
    # Fernet derives its internal signing/encryption keys from the provided
    # key material; the round-trip is the contract we care about. Assert that
    # the resolved key matches the derived-from-SECRET_KEY key by rebuilding
    # an equivalent Fernet and round-tripping the same ciphertext.
    assert isinstance(f, Fernet)
    enc = crypto.encrypt("fallback-secret")
    assert crypto.decrypt(enc) == "fallback-secret"
    # And an independently-built Fernet with the expected derived key can
    # decrypt ciphertext produced by resolve_fernet() (proves the derivation).
    twin = Fernet(expected_key)
    assert twin.decrypt(enc[len(crypto.ENC_PREFIX) :].encode("ascii")).decode("utf-8") == "fallback-secret"


def test_no_credential_key_and_no_fallback_raises():
    _set_config(credential_key="", fallback=False)
    with pytest.raises(crypto.EncryptionError):
        crypto.resolve_fernet()


def test_invalid_credential_key_raises():
    _set_config(credential_key="not-a-fernet-key")
    with pytest.raises(crypto.EncryptionError):
        crypto.resolve_fernet()


def test_encrypt_then_decrypt_different_key_raises():
    """Decrypting with a different key than was used to encrypt raises."""
    key1 = base64.urlsafe_b64encode(b"1" * 32).decode("ascii")
    _set_config(credential_key=key1)
    enc = crypto.encrypt("secret-with-key1")
    key2 = base64.urlsafe_b64encode(b"2" * 32).decode("ascii")
    _set_config(credential_key=key2)
    with pytest.raises(crypto.EncryptionError):
        crypto.decrypt(enc)

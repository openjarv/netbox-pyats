"""Tests for :mod:`netbox_pyats.crypto`.

Pure-Python: exercises key resolution (configured vs SECRET_KEY fallback),
round-trip encryption, and the empty-string round-trip path. Runs both inside
and outside a NetBox test environment.
"""

import base64
import hashlib
import warnings
from cryptography.fernet import Fernet
from django.conf import settings
from django.test import SimpleTestCase, override_settings
from netbox_pyats import crypto


class GetFernetKeyTest(SimpleTestCase):
    def _set_config(self, cfg):
        # override_settings works on PLUGINS_CONFIG because it's a Django
        # setting; we need the plugin's _get_config() to see our value.
        return override_settings(PLUGINS_CONFIG={"netbox_pyats": cfg})

    def test_configured_key_used_when_set(self):
        key = Fernet.generate_key()
        with self._set_config({"credential_key": key.decode("utf-8")}):
            self.assertEqual(crypto.get_fernet_key(), key)

    def test_configured_key_invalid_raises_improperly_configured(self):
        from django.core.exceptions import ImproperlyConfigured

        with self._set_config({"credential_key": "not-a-valid-fernet-key"}):
            with self.assertRaises(ImproperlyConfigured):
                crypto.get_fernet_key()

    def test_fallback_to_secret_key_warns(self):
        # No credential_key configured: must fall back to SECRET_KEY-derived key.
        with self._set_config({}):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                key = crypto.get_fernet_key()
            self.assertTrue(len(key) > 0)
            self.assertTrue(
                any(issubclass(w.category, RuntimeWarning) for w in caught),
                f"expected a RuntimeWarning fallback, got {[w.category for w in caught]}",
            )

    def test_fallback_key_matches_sha256_of_secret_key_slice(self):
        expected = base64.urlsafe_b64encode(
            hashlib.sha256((settings.SECRET_KEY or "").ljust(64, "_")[:64].encode("utf-8")).digest()
        )
        with self._set_config({}):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.assertEqual(crypto.get_fernet_key(), expected)


class EncryptDecryptTest(SimpleTestCase):
    def _config(self, cfg):
        return override_settings(PLUGINS_CONFIG={"netbox_pyats": cfg})

    def test_round_trip(self):
        key = Fernet.generate_key()
        with self._config({"credential_key": key.decode("utf-8")}):
            token = crypto.encrypt("hunter2")
            self.assertNotEqual(token, "hunter2")
            self.assertTrue(crypto.is_encrypted_token(token))
            self.assertEqual(crypto.decrypt(token), "hunter2")

    def test_empty_string_round_trips(self):
        key = Fernet.generate_key()
        with self._config({"credential_key": key.decode("utf-8")}):
            self.assertEqual(crypto.encrypt(""), "")
            self.assertEqual(crypto.decrypt(""), "")

    def test_none_treated_as_empty(self):
        key = Fernet.generate_key()
        with self._config({"credential_key": key.decode("utf-8")}):
            self.assertEqual(crypto.encrypt(None), "")
            self.assertEqual(crypto.decrypt(None), "")

    def test_decrypt_with_wrong_key_raises_invalid_token(self):
        from cryptography.fernet import InvalidToken

        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        with self._config({"credential_key": key1.decode("utf-8")}):
            token = crypto.encrypt("secret")
        with self._config({"credential_key": key2.decode("utf-8")}):
            with self.assertRaises(InvalidToken):
                crypto.decrypt(token)

    def test_is_encrypted_token_shape(self):
        key = Fernet.generate_key()
        with self._config({"credential_key": key.decode("utf-8")}):
            token = crypto.encrypt("x")
            self.assertTrue(crypto.is_encrypted_token(token))
        self.assertFalse(crypto.is_encrypted_token(""))
        self.assertFalse(crypto.is_encrypted_token("plaintext-not-a-token"))


class KeyRotationSensitivityTest(SimpleTestCase):
    """Document the v1 key-rotation contract: a new key cannot decrypt old tokens.

    This is the property that makes key rotation require re-keying existing
    credentials (documented in the crypto module and the README). The test
    pins it so a future refactor doesn't silently break the contract.
    """

    def test_new_key_cannot_decrypt_old_token(self):
        from cryptography.fernet import InvalidToken

        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"credential_key": key1.decode()}}):
            token = crypto.encrypt("legacy")
        with override_settings(PLUGINS_CONFIG={"netbox_pyats": {"credential_key": key2.decode()}}):
            with self.assertRaises(InvalidToken):
                crypto.decrypt(token)

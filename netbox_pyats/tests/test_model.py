"""Integration-style tests for the :class:`PyatsCredential` model.

These require NetBox (and the dcim.Device FK), so they skip cleanly via
``pytest.importorskip("netbox")`` when NetBox isn't installed. The pure-Python
credential encryption logic is covered separately in ``test_crypto.py``.
"""

import pytest

netbox = pytest.importorskip("netbox")  # noqa: F841

from netbox_pyats.models import PyatsCredential  # noqa: E402


@pytest.mark.django_db
def test_credential_encrypts_password_on_save_and_decrypts_on_read(db):
    cred = PyatsCredential(name="r1-creds", username="admin")
    cred.set_password("plain-pw")
    cred.set_enable_secret("enable-pw")
    cred.save()

    # Stored fields are encrypted at rest (prefixed + not plaintext).
    assert cred.password.startswith("ENC1:")
    assert "plain-pw" not in cred.password
    assert cred.enable_secret.startswith("ENC1:")
    assert "enable-pw" not in cred.enable_secret

    # Plaintext round-trips via the getters.
    assert cred.get_password() == "plain-pw"
    assert cred.get_enable_secret() == "enable-pw"


@pytest.mark.django_db
def test_credential_update_keeps_existing_secret_when_blank(db):
    cred = PyatsCredential(name="r2-creds", username="admin")
    cred.set_password("first-pw")
    cred.save()

    # Re-fetch and save without supplying a new password; existing ciphertext
    # should be retained, not wiped.
    cred.refresh_from_db()
    cred.save()
    cred.refresh_from_db()
    assert cred.password.startswith("ENC1:")
    assert cred.get_password() == "first-pw"

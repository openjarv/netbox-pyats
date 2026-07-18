"""pytest configuration for netbox_pyats tests.

Two modes (mirrors the netbox_atw pattern):

1. **Inside NetBox** (integration / model / view / API tests): when ``netbox``
   is importable we defer to NetBox's own Django settings via
   ``DJANGO_SETTINGS_MODULE=netbox.settings``.
2. **Outside NetBox** (pure-Python tests): configure minimal Django settings so
   the credential-encryption and testbed-builder logic runs without a full
   NetBox dev instance. NetBox-dependent test files skip themselves via
   ``pytest.importorskip("netbox")``.
"""

import os

import django
from django.conf import settings


def _netbox_available() -> bool:
    try:
        import netbox  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _configure_minimal():
    """Minimal Django config for pure-Python tests (no NetBox installed)."""
    if settings.configured:
        return
    settings.configure(
        DEBUG=False,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "netbox_pyats",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        USE_TZ=True,
        SECRET_KEY="test-secret-key-for-pyats-plugin-0123456789-abcdefghij",
        PLUGINS_CONFIG={
            "netbox_pyats": {
                "credential_key": "",
                "credential_key_fallback_to_secret_key": True,
            }
        },
    )
    django.setup()


def _configure_netbox():
    """Use NetBox's own settings when running inside a NetBox environment."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netbox.settings")
    if not settings.configured:
        django.setup()


if _netbox_available():
    _configure_netbox()
else:
    _configure_minimal()

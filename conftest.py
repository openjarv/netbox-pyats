"""pytest configuration for netbox_pyats tests.

Two modes, matching the netbox-atw scaffold pattern:

1. **Inside NetBox** (integration / model / view / API tests): when ``netbox``
   is importable we defer to NetBox's own Django settings via
   ``DJANGO_SETTINGS_MODULE=netbox.settings``.
2. **Outside NetBox** (pure-Python tests): configure a minimal Django settings
   module (in-memory SQLite) so the crypto helpers, platform-to-os mapping,
   and the testbed builder (with pyATS installed) can run without a full NetBox
   dev instance. The plugin app is NOT added to INSTALLED_APPS in minimal mode
   because ``models.py`` imports ``netbox.models.NetBoxModel`` (which is only
   available inside NetBox). The pure-Python tests only exercise modules that
   do not import ``models.py`` (crypto + testbed builder), so this is safe.
   The NetBox-dependent test files skip themselves via
   ``pytest.importorskip("netbox")``.

This dual-mode setup lets the same test tree run fast anywhere (laptop, CI unit
job) and fully inside a NetBox dev container.
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
    """Minimal Django config for pure-Python tests (no NetBox installed).

    ``netbox_pyats`` is intentionally NOT in INSTALLED_APPS here because
    ``models.py`` imports ``netbox.models.NetBoxModel`` which is unavailable
    outside NetBox. The pure-Python tests only touch ``crypto`` and
    ``testbed`` (which lazy-imports ``models``), so Django's app registry is
    not needed for them. ``settings.configure`` is still required because
    ``crypto.py`` reads ``settings.PLUGINS_CONFIG`` and ``settings.SECRET_KEY``.
    """
    if settings.configured:
        return
    settings.configure(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        USE_TZ=True,
        SECRET_KEY="dev-only-not-for-production-CHANGE-ME-0123456789-abcdefghij",
        PLUGINS_CONFIG={
            "netbox_pyats": {},
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

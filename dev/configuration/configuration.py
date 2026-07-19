# NetBox dev configuration for netbox-pyats.
# Minimal config that enables the plugin and is safe for local dev only.

ALLOWED_HOSTS = ["*"]
SECRET_KEY = "dev-only-not-for-production-CHANGE-ME-0123456789-abcdefghij-0123456789-abcdefghij"
# DEBUG=False keeps the dev config usable for both serving the UI and running
# `manage.py test`: NetBox installs the debug toolbar only when DEBUG=True, and
# the toolbar's E001 system check errors out under Django's test runner (which
# forces DEBUG=False). DEBUG=False avoids that without affecting plugin dev.
DEBUG = False

DATABASE = {
    "NAME": "netbox",
    "USER": "netbox",
    "PASSWORD": "netbox",
    "HOST": "postgres",
    "PORT": 5432,
    "CONN_MAX_AGE": 300,
}

REDIS = {
    "tasks": {
        "HOST": "redis",
        "PORT": 6379,
        "PASSWORD": "",
    },
    "caching": {
        "HOST": "redis",
        "PORT": 6379,
        "PASSWORD": "",
    },
}

PLUGINS = [
    "netbox_pyats",
]

PLUGINS_CONFIG = {
    "netbox_pyats": {
        # Dev: no dedicated credential_key configured; the plugin will derive
        # one from SECRET_KEY (with a RuntimeWarning). Set this for any test
        # that asserts key-rotation behavior or for production.
        "credential_key": "",
    },
}

# v2 API tokens require at least one pepper. NetBox's APITestCase creates a
# Token in setUp, which calls get_current_pepper() and raises ValueError if
# API_TOKEN_PEPPERS is unset. Dev-only; never ship this key in production.
API_TOKEN_PEPPERS = {
    1: "dev-only-not-for-production-CHANGE-ME-test-pepper-0123456789-abcdefghij",
}
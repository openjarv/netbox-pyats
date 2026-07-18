"""netbox_pyats — Atw NetBox plugin that brings Cisco PyATS/Genie into NetBox."""

from .version import __version__

try:
    from netbox.plugins import PluginConfig
except ModuleNotFoundError:  # pragma: no cover - allows importing submodules without NetBox installed
    PluginConfig = object  # type: ignore[misc,assignment]


class PyatsConfig(PluginConfig):
    name = "netbox_pyats"
    verbose_name = "PyATS"
    description = "Cisco PyATS/Genie in NetBox: device snapshots, structured diffs, and config compliance."
    version = __version__
    base_url = "pyats"
    min_version = "3.5.0"
    default_settings = {
        # Recommended: dedicated Fernet key for credential encryption.
        # Generate with:
        #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        "credential_key": "",
        # Whether to fall back to a slice of NetBox SECRET_KEY when
        # credential_key is not set. Defaults to True so the plugin works
        # out of the box, but operators are encouraged to set a dedicated key.
        "credential_key_fallback_to_secret_key": True,
    }


config = PyatsConfig

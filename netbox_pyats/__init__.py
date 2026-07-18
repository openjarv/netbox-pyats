from .version import __version__

try:
    from netbox.plugins import PluginConfig
except ModuleNotFoundError:  # pragma: no cover - allows importing submodules without NetBox installed
    PluginConfig = object  # type: ignore[misc,assignment]


class NetBoxPyATSConfig(PluginConfig):
    name = "netbox_pyats"
    verbose_name = "PyATS"
    description = (
        "Brings Cisco PyATS/Genie into NetBox: dynamic testbed building from the NetBox ORM, "
        "plugin-local encrypted credentials, and (in later phases) device snapshots, structured "
        "diffs, and config compliance from the device page."
    )
    version = __version__
    base_url = "pyats"
    min_version = "3.5.0"

    # Plugin-local configuration schema (validated by NetBox at startup).
    # `credential_key` is the recommended Fernet key for encrypting credential
    # secrets. If absent, the plugin derives a stable key from a slice of the
    # NetBox `SECRET_KEY` (documented as a fallback for dev only).
    default_settings = {
        "credential_key": "",
    }


config = NetBoxPyATSConfig

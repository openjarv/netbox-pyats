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

    # Dedicated RQ queue for pyATS/Genie work. The capture/diff/compliance jobs
    # require `pyats[full]` installed on the worker, which the default NetBox
    # worker container does not have. Declaring the queue here makes NetBox
    # create it at startup; operators run a second worker pointed at `pyats`
    # (see dev/docker-compose.dev.yml `netbox-pyats-worker` and the worker
    # Dockerfile). Keeping pyATS work off the default queue means a long
    # device capture run can never block NetBox's own housekeeping jobs.
    queues = ["pyats"]

    # Inject the PyATS capture panel + recent-snapshots list into the Device
    # detail page (Phase 2, ATW-13). The dotted path is resolved by NetBox at
    # startup; the module exposes a `template_extensions` list.
    template_extensions = "template_content.template_extensions"

    # Plugin-local configuration schema (validated by NetBox at startup).
    # `credential_key` is the recommended Fernet key for encrypting credential
    # secrets. If absent, the plugin derives a stable key from a slice of the
    # NetBox `SECRET_KEY` (documented as a fallback for dev only).
    default_settings = {
        "credential_key": "",
    }


config = NetBoxPyATSConfig

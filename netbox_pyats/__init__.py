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

    # Single consolidated top-level PluginMenu (ATW-794). The ATW-728 split
    # into ``genie_menu`` + ``jobs_menu`` is folded back into one
    # ``navigation.menu`` labeled "PyATS/Genie" with both Genie and PyATS
    # items grouped underneath (Jobs & Platforms last, supported_platforms
    # final per ADR-0001 §3 / ATW-83). PluginConfig._load_resource imports
    # ``{module}.{menu}``, so point it at the consolidated menu; no
    # ``ready()`` register_menu override is needed with a single menu.
    menu = "navigation.menu"

    # Plugin-local configuration schema (validated by NetBox at startup).
    # `credential_key` is the recommended Fernet key for encrypting credential
    # secrets. If absent, the plugin derives a stable key from a slice of the
    # NetBox `SECRET_KEY` (documented as a fallback for dev only).
    default_settings = {
        "credential_key": "",
        # Per-OS state-capture command override. When set, the automated
        # kind='state'/'full' capture runs these commands instead of the
        # OS-agnostic STATE_COMMANDS default for the matching os. Format:
        # {"nxos": ["show version", "show vlan"], "iosxe": ["show platform"]}.
        # An os with no entry falls back to STATE_COMMANDS. Additive per os,
        # not per command — listing an os replaces (not extends) the default
        # set for that os. See netbox_pyats.capture.resolve_state_commands.
        "state_commands_per_os": {},
    }


config = NetBoxPyATSConfig

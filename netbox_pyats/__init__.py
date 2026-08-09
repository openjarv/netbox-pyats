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

    # The ATW-728 Genie nav restructure splits the single PyATS menu into two
    # top-level PluginMenus: ``genie_menu`` (the primary surface — Genie Tools
    # with Parse/Learn/Diff, plus the supporting groups) and ``jobs_menu``
    # (the operational surface — PyATS Jobs + the static supported-platforms
    # report). PluginConfig._load_resource imports ``{module}.{menu}``, so
    # point the default ``menu`` at ``navigation.genie_menu``; ``jobs_menu``
    # is registered explicitly in ``ready()`` below.
    menu = "navigation.genie_menu"

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

    def ready(self):
        super().ready()
        # The default PluginConfig.ready() registers only the module-level
        # ``navigation.menu`` PluginMenu. The ATW-728 Genie nav restructure
        # registers a second top-level menu (``navigation.jobs_menu``) — the
        # operational surface (PyATS Jobs + the static supported-platforms
        # report) that the prior single PyATS menu carried alongside the
        # Genie tools. register_menu is idempotent per call: each call
        # appends one PluginMenu to the plugin menu registry.
        try:
            from netbox.plugins.registration import register_menu
        except ModuleNotFoundError:  # pragma: no cover - netbox.plugins absent
            return
        from .navigation import jobs_menu

        register_menu(jobs_menu)


config = NetBoxPyATSConfig

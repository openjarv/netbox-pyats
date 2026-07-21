from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenuItem

menu_items = [
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatscredential_list",
        link_text=_("PyATS Credentials"),
        permissions=["netbox_pyats.view_pyatscredential"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatscredential_add",
        link_text=_("Add Credential"),
        permissions=["netbox_pyats.add_pyatscredential"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatssnapshot_list",
        link_text=_("PyATS Snapshots"),
        permissions=["netbox_pyats.view_pyatssnapshot"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatssnapshotdiff_list",
        link_text=_("PyATS Snapshot Diffs"),
        permissions=["netbox_pyats.view_pyatssnapshotdiff"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatsgoldenconfig_list",
        link_text=_("PyATS Golden Configs"),
        permissions=["netbox_pyats.view_pyatsgoldenconfig"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatscompliancerun_list",
        link_text=_("PyATS Compliance Runs"),
        permissions=["netbox_pyats.view_pyatscompliancerun"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatsjob_list",
        link_text=_("PyATS Jobs"),
        permissions=["netbox_pyats.view_pyatsjob"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatscompliancerun_list",
        link_text=_("PyATS Compliance Runs"),
        permissions=["netbox_pyats.view_pyatscompliancerun"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:pyatsjob_list",
        link_text=_("PyATS Jobs"),
        permissions=["netbox_pyats.view_pyatsjob"],
    ),
    PluginMenuItem(
        link="plugins:netbox_pyats:supported_platforms",
        link_text=_("Supported Platforms"),
        permissions=["netbox_pyats.view_pyatsjob"],
    ),
]

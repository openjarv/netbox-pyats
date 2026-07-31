from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuItem

# Top-level plugin menu (replaces the flat ``menu_items`` list that NetBox
# nested under the built-in Plugins dropdown). NetBox v4.6 PluginMenu takes
# ``(label, groups, icon_class=None)`` where ``groups`` is a list of
# ``(group_label, [PluginMenuItem, ...])`` tuples. Each group renders as a
# labelled section inside the top-level "PyATS" nav entry.
#
# Ordering convention (ADR-0001 §3 / ATW-83): the static ``supported_platforms``
# report (the only non-model menu entry) is last overall.
menu = PluginMenu(
    label=_("PyATS"),
    groups=(
        (
            _("Credentials"),
            (
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
            ),
        ),
        (
            _("Snapshots & Diffs"),
            (
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
            ),
        ),
        (
            _("Golden Configs & Compliance"),
            (
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
            ),
        ),
        (
            _("Jobs & Platforms"),
            (
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
            ),
        ),
    ),
    icon_class="mdi mdi-router-wireless",
)

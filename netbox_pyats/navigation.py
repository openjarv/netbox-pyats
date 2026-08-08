from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuItem

# Two top-level plugin menus: ``genie_menu`` leads with the three primary
# Genie tools (Parse / Learn / Diff, ATW-727) and carries the supporting
# groups; ``jobs_menu`` holds the operational surface (job history and the
# static supported-platforms report). NetBox v4.6 ``PluginMenu`` takes
# ``(label, groups, icon_class=None)`` where ``groups`` is a list of
# ``(group_label, [PluginMenuItem, ...])`` tuples. Each group renders as a
# labelled section inside the top-level nav entry.
#
# Interim routing (ATW-728 — navigation restructure; the full dedicated
# Genie pages ship in the ATW-729/730/731 child issues):
#   * Genie Parse → a device-picker landing page (``genie_parse``) that
#     redirects into the per-device parse sub-tab (ATW-241/250). Parse is
#     inherently per-device, so the top-level entry resolves the device first.
#     Permissions reuse ``add_pyatssnapshot`` — the parse result lands as a
#     ``kind='parse'`` PyatsSnapshot row, so that is the gate the underlying
#     per-device view enforces (no separate parse model).
#   * Genie Learn → a landing page (``genie_learn``) rendering the parser
#     catalog — the learned capability state the refresh job stores as
#     PyatsParserCatalog rows (ATW-581). The dedicated Learn page replaces
#     this entry in ATW-730.
#   * Genie Diff → the snapshot-diff list (ATW-243). Diff already has a
#     full list view; ATW-731 promotes it to a dedicated page.
#
# Ordering convention (ADR-0001 §3 / ATW-83): the static ``supported_platforms``
# report (the only non-model menu entry) is last overall — it closes the
# Jobs & Platforms menu.
genie_menu = PluginMenu(
    label=_("Genie"),
    groups=(
        (
            _("Genie Tools"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:genie_parse",
                    link_text=_("Genie Parse"),
                    permissions=["netbox_pyats.add_pyatssnapshot"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:genie_learn",
                    link_text=_("Genie Learn"),
                    permissions=["netbox_pyats.view_pyatssnapshot"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatssnapshotdiff_list",
                    link_text=_("Genie Diff"),
                    permissions=["netbox_pyats.view_pyatssnapshotdiff"],
                ),
            ),
        ),
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
            _("Snapshots"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatssnapshot_list",
                    link_text=_("PyATS Snapshots"),
                    permissions=["netbox_pyats.view_pyatssnapshot"],
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
            _("Capture Schedules"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatscaptureschedule_list",
                    link_text=_("PyATS Capture Schedules"),
                    permissions=["netbox_pyats.view_pyatscaptureschedule"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatscaptureschedule_add",
                    link_text=_("Add Capture Schedule"),
                    permissions=["netbox_pyats.add_pyatscaptureschedule"],
                ),
            ),
        ),
        (
            _("Parser Catalog"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatsparsercatalogrefreshschedule_list",
                    link_text=_("Catalog Refresh Schedule"),
                    permissions=["netbox_pyats.view_pyatsparsercatalogrefreshschedule"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatsparsercatalogrefreshschedule_add",
                    link_text=_("Edit Refresh Schedule"),
                    permissions=["netbox_pyats.add_pyatsparsercatalogrefreshschedule"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-router-wireless",
)

jobs_menu = PluginMenu(
    label=_("PyATS Jobs & Platforms"),
    groups=(
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
    icon_class="mdi mdi-format-list-checkbox",
)

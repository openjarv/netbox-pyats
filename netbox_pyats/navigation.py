from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuItem

# Single top-level plugin menu (ATW-794 consolidation): ``menu`` carries the
# full PyATS/Genie surface under one labelled "PyATS/Genie" entry, replacing
# the ATW-728 dual-menu split (``genie_menu`` + ``jobs_menu``). NetBox v4.6
# ``PluginMenu`` takes ``(label, groups, icon_class=None)`` where ``groups``
# is a list of ``(group_label, [PluginMenuItem, ...])`` tuples. Each group
# renders as a labelled section inside the top-level nav entry.
#
# The ATW-728 split was originally introduced to give Genie its own top-level
# surface alongside PyATS Jobs; the board's ATW-794 direction is a single
# top-level entry with both Genie and PyATS items grouped underneath, so the
# two menus fold back together and the ``jobs_menu`` group lands as
# "Jobs & Platforms" (last group, keeping supported_platforms the final item
# per ADR-0001 §3 / ATW-83).
#
# Routing (post ATW-728/729/730/731/794):
#   * Genie Parse → the dedicated Genie Parse page (``genie_parse``,
#     ATW-729) — a device picker + on-demand parse form + recent parse
#     results, all on one first-class page. Permissions reuse
#     ``add_pyatssnapshot`` — the parse result lands as a
#     ``kind='parse'`` PyatsSnapshot row, so that is the gate the
#     underlying view enforces (no separate parse model).
#   * Genie Learn → the dedicated Genie Learn page (``genie_learn``,
#     ATW-730) — the parser catalog (learned capability state) + a device
#     picker + Run Learn action + recent learn results. The Learn job
#     drives the Genie Ops framework on the worker and stores a
#     ``kind='learn'`` PyatsSnapshot row. Permissions reuse
#     ``add_pyatssnapshot`` (the learn result lands as a snapshot) +
#     ``view_pyatssnapshot`` (the catalog + recent-results table read rows).
#   * Genie Diff → the dedicated Genie Diff page (``genie_diff``, ATW-731) —
#     the primary surface for all diff operations: same-device snapshot diff,
#     cross-device diff, and recent diffs. The full diff history remains on
#     ``pyatssnapshotdiff_list`` (linked from the Diff page, not in the nav
#     menu — the standalone menu entry was redundant once the dedicated Diff
#     page shipped, ATW-728/731).
# Ordering convention (ADR-0001 §3 / ATW-83): the static ``supported_platforms``
# report (the only non-model menu entry) is last overall — it closes the
# Jobs & Platforms group.
menu = PluginMenu(
    label=_("PyATS/Genie"),
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
                    permissions=["netbox_pyats.add_pyatssnapshot", "netbox_pyats.view_pyatssnapshot"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:genie_diff",
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
                    link_text=_("Credentials"),
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
                    link_text=_("Snapshots"),
                    permissions=["netbox_pyats.view_pyatssnapshot"],
                ),
            ),
        ),
        (
            _("Golden Configs & Compliance"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatsgoldenconfig_list",
                    link_text=_("Golden Configs"),
                    permissions=["netbox_pyats.view_pyatsgoldenconfig"],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatscompliancerun_list",
                    link_text=_("Compliance Runs"),
                    permissions=["netbox_pyats.view_pyatscompliancerun"],
                ),
            ),
        ),
        (
            _("Automation"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatscaptureschedule_list",
                    link_text=_("Capture Schedules"),
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
        (
            _("Jobs & Platforms"),
            (
                PluginMenuItem(
                    link="plugins:netbox_pyats:pyatsjob_list",
                    link_text=_("Jobs"),
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

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
# Relabel pass (ATW-732): the supporting infrastructure moved under the Genie
# menu in ATW-728, so the redundant ``PyATS`` prefix is dropped from the
# ``link_text`` of every supporting item (the menu already says "Genie").
# The "Capture Schedules" group is renamed to "Automation" to match the
# board's proposed final navigation (ATW-727 plan). No links, permissions,
# or ordering changed — this is a display-text-only consolidation. The
# standalone ``pyatssnapshotdiff_list`` menu entry was already removed in
# ATW-728 (the list view remains at /diffs/ as the full-history target
# linked from the Genie Diff page, ATW-731).
#
# Routing (post ATW-728/729/730/731):
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

jobs_menu = PluginMenu(
    label=_("PyATS Jobs & Platforms"),
    groups=(
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
    icon_class="mdi mdi-format-list-checkbox",
)

"""Navigation menu entries for the netbox_pyats plugin."""

from django.utils.translation import gettext_lazy as _

try:
    from netbox.plugins import PluginMenuItem
except ModuleNotFoundError:  # pragma: no cover - importable without netbox
    PluginMenuItem = None  # type: ignore[assignment]


if PluginMenuItem is not None:
    menu_items = [
        PluginMenuItem(
            link="plugins:netbox_pyats:pyatscredential_list",
            link_text=_("PyATS Credentials"),
            permissions=["netbox_pyats.view_pyatscredential"],
        ),
        PluginMenuItem(
            link="plugins:netbox_pyats:pyatscredential_add",
            link_text=_("New Credential"),
            permissions=["netbox_pyats.add_pyatscredential"],
        ),
    ]
else:  # pragma: no cover - only hit when netbox is not installed
    menu_items = []

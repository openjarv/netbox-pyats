"""Choice sets for the netbox-pyats plugin."""

from django.db import models


class CredentialProtocolChoices(models.TextChoices):
    """Connection protocol for a PyATS credential."""

    PROTOCOL_SSH = "ssh", "SSH"
    PROTOCOL_TELNET = "telnet", "Telnet"
    PROTOCOL_CONSOLE = "console", "Console"


class CredentialScopeChoices(models.TextChoices):
    """How a credential is assigned.

    ``device`` credentials attach to a single NetBox Device (1:1). ``global``
    credentials are not bound to a specific device and can be referenced by name
    from a testbed build (useful for shared lab creds). v1 only ships ``device``
    scope; ``global`` is reserved for the bulk-snapshot flow in ATW-13.
    """

    SCOPE_DEVICE = "device", "Per device"
    SCOPE_GLOBAL = "global", "Global (shared)"

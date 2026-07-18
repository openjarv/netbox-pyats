"""Choice sets for the netbox_pyats plugin."""

from django.db import models


class CredentialProtocolChoices(models.TextChoices):
    """Transport protocol used to reach a device for pyATS connections."""

    PROTOCOL_SSH = "ssh", "SSH"
    PROTOCOL_TELNET = "telnet", "Telnet"
    PROTOCOL_CONSOLE = "console", "Console"

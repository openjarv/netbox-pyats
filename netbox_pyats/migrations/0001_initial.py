from django.db import migrations, models

import netbox_pyats.choices


class Migration(migrations.Migration):

    initial = True

    # NetBox plugin convention: do not pin to a specific dcim migration.
    # The previous pin to dcim.0050_custom_field_choice_set_remove referenced
    # a migration that does not exist in any released NetBox 4.6.x image, which
    # broke `manage.py migrate` (NodeNotFoundError). `dependencies = []` is the
    # durable form (matches netbox/netbox/tests/dummy_plugin). See ATW-25 / ADR-0003.
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PyatsCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "name",
                    models.CharField(help_text="Human-readable label, e.g. 'rtr01-ssh'.", max_length=100),
                ),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        help_text="NetBox device this credential targets. Null for global/shared creds.",
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="pyats_credentials",
                        to="dcim.device",
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=netbox_pyats.choices.CredentialScopeChoices.choices,
                        default="device",
                        help_text="Per-device (1:1) or global/shared credential.",
                        max_length=20,
                    ),
                ),
                (
                    "username",
                    models.CharField(help_text="Login username for SSH/Telnet/Console.", max_length=100),
                ),
                (
                    "password",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Encrypted Fernet token. Set via set_password(); do not write plaintext here.",
                        max_length=512,
                    ),
                ),
                (
                    "enable_secret",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Encrypted Fernet token for the enable/privileged password. Optional.",
                        max_length=512,
                    ),
                ),
                (
                    "ssh_port",
                    models.PositiveIntegerField(default=22, help_text="TCP port for SSH/Telnet connections."),
                ),
                (
                    "protocol",
                    models.CharField(
                        choices=netbox_pyats.choices.CredentialProtocolChoices.choices,
                        default="ssh",
                        help_text="Connection protocol pyATS/Unicon should use.",
                        max_length=20,
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True, related_name="extras_tag_netbox_pyats_pyatscredential", to="extras.tag"
                    ),
                ),
            ],
            options={
                "verbose_name": "PyATS Credential",
                "verbose_name_plural": "PyATS Credentials",
                "ordering": ("device__name", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="pyatscredential",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=False),
                fields=("device", "name"),
                name="netbox_pyats_credential_unique_per_device",
            ),
        ),
        migrations.AddConstraint(
            model_name="pyatscredential",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=True),
                fields=("name",),
                name="netbox_pyats_credential_unique_global_name",
            ),
        ),
    ]

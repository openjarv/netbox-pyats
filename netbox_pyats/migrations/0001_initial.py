from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # FK to dcim.Device. 0001_squashed is the baseline dcim migration on
        # NetBox 4.6+. Operators who regenerate migrations against a specific
        # NetBox version will get the latest dcim migration name substituted in
        # by `makemigrations`.
        ("dcim", "0001_squashed"),
    ]

    operations = [
        migrations.CreateModel(
            name="PyatsCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                ("name", models.CharField(help_text="Human-readable label for this credential.", max_length=100)),
                ("username", models.CharField(max_length=100)),
                (
                    "password",
                    models.CharField(
                        help_text="Encrypted at rest with Fernet. Set the plaintext value; it is encrypted on save.",
                        max_length=512,
                    ),
                ),
                (
                    "enable_secret",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Optional enable secret. Encrypted at rest with Fernet.",
                        max_length=512,
                    ),
                ),
                ("ssh_port", models.PositiveIntegerField(default=22, help_text="SSH/Telnet TCP port.")),
                (
                    "protocol",
                    models.CharField(
                        choices=[
                            ("ssh", "SSH"),
                            ("telnet", "Telnet"),
                            ("console", "Console"),
                        ],
                        default="ssh",
                        help_text="Transport protocol used for the pyATS connection.",
                        max_length=10,
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        help_text="Device this credential applies to. Leave blank for a group/shared credential.",
                        null=True,
                        on_delete=models.CASCADE,
                        related_name="pyats_credentials",
                        to="dcim.device",
                    ),
                ),
            ],
            options={
                "ordering": ("name", "device__name"),
                "verbose_name": "PyATS Credential",
                "verbose_name_plural": "PyATS Credentials",
            },
        ),
        migrations.AddConstraint(
            model_name="pyatscredential",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=False),
                fields=("device",),
                name="netbox_pyats_credential_one_per_device",
            ),
        ),
    ]

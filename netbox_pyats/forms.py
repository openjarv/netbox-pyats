"""Forms for the netbox_pyats plugin.

The credential form accepts plaintext secrets and hands them to the model's
:meth:`PyatsCredential.set_password` / :meth:`set_enable_secret`, which encrypt
on save. Plaintext is never persisted.
"""

from django import forms

from .choices import CredentialProtocolChoices
from .models import PyatsCredential


class PyatsCredentialForm(forms.ModelForm):
    """Create/edit form for PyatsCredential.

    Plaintext secret fields are :class:`CharField` widgets with render_value
    disabled (default) so they don't survive a validation error round-trip.
    The model's encryption helpers handle the at-rest encryption.
    """

    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Plaintext password. Encrypted at rest on save. Leave blank when editing to keep the existing value.",
    )
    enable_secret = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text=(
            "Optional enable secret. Encrypted at rest on save. " "Leave blank when editing to keep the existing value."
        ),
    )

    class Meta:
        model = PyatsCredential
        fields = [
            "name",
            "device",
            "username",
            "password",
            "enable_secret",
            "ssh_port",
            "protocol",
            "tags",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On edit, password/enable_secret are blank; existing ciphertext stays
        # untouched unless the user types a new value.
        if self.instance and self.instance.pk:
            self.fields["password"].required = False
            self.fields["enable_secret"].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("password") and self.instance and self.instance.pk:
            # No new password supplied on edit; keep existing ciphertext.
            cleaned["password"] = self.instance.password
        if not cleaned.get("enable_secret") and self.instance and self.instance.pk:
            cleaned["enable_secret"] = self.instance.enable_secret
        return cleaned

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get("password")
        enable_secret = self.cleaned_data.get("enable_secret") or ""
        # Only push plaintext through the encrypt-on-save path if a new value
        # was typed. If we're keeping existing ciphertext, leave the model
        # field alone (it's already encrypted and idempotent under encrypt()).
        if password and not password.startswith("ENC1:"):
            instance.set_password(password)
        elif password and password.startswith("ENC1:") and password != instance.password:
            # Existing ciphertext re-supplied (rare); keep as-is.
            instance.password = password
        if enable_secret and not enable_secret.startswith("ENC1:"):
            instance.set_enable_secret(enable_secret)
        elif enable_secret and enable_secret.startswith("ENC1:") and enable_secret != instance.enable_secret:
            instance.enable_secret = enable_secret
        if commit:
            instance.save()
        return instance


class PyatsCredentialFilterForm(forms.Form):
    """Filter form for the PyatsCredential list view."""

    model = PyatsCredential

    q = forms.CharField(required=False, label="Search")
    protocol = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + CredentialProtocolChoices.choices,
    )

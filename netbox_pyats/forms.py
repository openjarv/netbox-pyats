from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm

from .choices import CredentialProtocolChoices, CredentialScopeChoices
from .models import PyatsCredential


class PyatsCredentialForm(NetBoxModelForm):
    """Create/edit form for a PyATS Credential.

    Plaintext password/enable_secret are accepted via dedicated form fields
    (``plaintext_password`` / ``plaintext_enable_secret``) so the encrypted
    ciphertext on the model is never rendered back to the user. On save the
    form calls the model's encryption setters; the ciphertext fields are
    never displayed in the UI.
    """

    plaintext_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="Device login password. Stored encrypted (Fernet). Leave blank to keep the existing password when editing.",
    )
    plaintext_enable_secret = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="Enable/privileged password. Optional. Stored encrypted (Fernet).",
    )

    fieldsets = (
        ("Credential", ("name", "scope", "device", "username", "plaintext_password", "plaintext_enable_secret")),
        ("Connection", ("protocol", "ssh_port")),
        ("Tags", ("tags",)),
    )

    class Meta:
        model = PyatsCredential
        fields = (
            "name",
            "scope",
            "device",
            "username",
            "protocol",
            "ssh_port",
            "tags",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tighten scope choices to what v1 actually supports.
        self.fields["scope"].choices = CredentialScopeChoices.choices

    def clean(self):
        super().clean()
        scope = self.cleaned_data.get("scope")
        device = self.cleaned_data.get("device")
        if scope == CredentialScopeChoices.SCOPE_DEVICE and not device:
            raise forms.ValidationError({"device": "A per-device credential must have a device assigned."})
        if scope == CredentialScopeChoices.SCOPE_GLOBAL and device:
            raise forms.ValidationError({"device": "A global credential must not be bound to a specific device."})
        # A device-scoped credential must have a username.
        if not self.cleaned_data.get("username"):
            raise forms.ValidationError({"username": "Username is required."})

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        plaintext_password = self.cleaned_data.get("plaintext_password") or ""
        plaintext_enable_secret = self.cleaned_data.get("plaintext_enable_secret") or ""
        # Only overwrite the ciphertext when a plaintext value was provided; on
        # edit with blank fields, keep the existing ciphertext (the model field
        # is unchanged because it's not in the form fields list).
        if plaintext_password:
            instance.set_password(plaintext_password)
        if plaintext_enable_secret:
            instance.set_enable_secret(plaintext_enable_secret)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PyatsCredentialFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsCredential list view."""

    model = PyatsCredential

    q = forms.CharField(required=False, label="Search")
    scope = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + CredentialScopeChoices.choices,
    )
    protocol = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + CredentialProtocolChoices.choices,
    )
    device = forms.IntegerField(required=False, label="Device ID")

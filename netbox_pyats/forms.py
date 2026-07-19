from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm

from .choices import (
    CredentialProtocolChoices,
    CredentialScopeChoices,
    DiffStatusChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from .models import PyatsCredential, PyatsSnapshot, PyatsSnapshotDiff


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


class PyatsSnapshotFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsSnapshot list view."""

    model = PyatsSnapshot

    q = forms.CharField(required=False, label="Search")
    device = forms.IntegerField(required=False, label="Device ID")
    kind = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + SnapshotKindChoices.choices,
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + SnapshotStatusChoices.choices,
    )
    triggered_by = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + SnapshotTriggerChoices.choices,
    )


class DeviceCaptureForm(forms.Form):
    """Form backing the device-page "Capture snapshot" button.

    Posted to the ``device_capture`` view. Only the ``kind`` is user-selectable;
    the device is in the URL, and ``triggered_by`` is always ``user`` for
    manual captures from the device page (automated flows enqueue directly).
    """

    kind = forms.ChoiceField(
        choices=SnapshotKindChoices.choices,
        initial=SnapshotKindChoices.KIND_FULL,
        required=True,
        label="Capture kind",
    )


class DeviceDiffForm(forms.Form):
    """Form backing the device-page "Diff two snapshots" picker (Phase 3).

    Posted to the ``device_diff`` view. The operator selects two snapshots of
    the same device; the view enqueues :func:`jobs.enqueue_diff`. The device is
    in the URL; ``before_id`` and ``after_id`` are validated by the view to
    belong to that device.
    """

    before_id = forms.IntegerField(required=True, label="Before snapshot")
    after_id = forms.IntegerField(required=True, label="After snapshot")


class PyatsSnapshotDiffFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsSnapshotDiff list view."""

    model = PyatsSnapshotDiff

    q = forms.CharField(required=False, label="Search")
    device = forms.IntegerField(required=False, label="Device ID")
    status = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + DiffStatusChoices.choices,
    )
    has_changes = forms.BooleanField(required=False, label="Only diffs with changes")
    has_warnings = forms.BooleanField(required=False, label="Only diffs with warnings")

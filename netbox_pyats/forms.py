from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.rendering import FieldSet

from .choices import (
    ComplianceModeChoices,
    ComplianceResultChoices,
    CredentialProtocolChoices,
    CredentialScopeChoices,
    DiffStatusChoices,
    GoldenConfigSourceChoices,
    PyatsJobStatusChoices,
    PyatsJobTypeChoices,
    SnapshotKindChoices,
    SnapshotStatusChoices,
    SnapshotTriggerChoices,
)
from .models import (
    PyatsCaptureSchedule,
    PyatsComplianceRun,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsJob,
    PyatsParserCatalogRefreshSchedule,
    PyatsSnapshot,
    PyatsSnapshotDiff,
)


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

    # NetBox 4.6's render_fieldset tag expects each fieldset entry to be a
    # FieldSet instance (with a .items attribute), not the legacy
    # ("name", (fields...)) tuple.
    fieldsets = (
        FieldSet(
            "name", "scope", "device", "username", "plaintext_password", "plaintext_enable_secret", name="Credential"
        ),
        FieldSet("protocol", "ssh_port", name="Connection"),
        FieldSet("tags", name="Tags"),
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

    ATW-241 child 4: the two snapshots must share the same ``kind``. A
    ``kind='parse'`` row is only diffable against another ``parse`` row (two
    manual parses of the same commands); a ``kind='state'``/`'full'`` row is
    only diffable against its own kind (different command sets). The template
    groups the picker options by ``kind`` via ``<optgroup>`` as a visual hint;
    this ``clean()`` is the actual filter enforcement (no JS, ADR-0001 §4).

    ATW-429: ``clean()`` scopes snapshot lookups by ``device`` when one is
    passed to ``__init__`` — defence-in-depth so a crafted POST cannot probe
    cross-instance snapshot ids. The view re-validates with
    ``device=device``; this form-level scope is the inner guard.
    """

    before_id = forms.IntegerField(required=True, label="Before snapshot")
    after_id = forms.IntegerField(required=True, label="After snapshot")

    def __init__(self, *args, device=None, **kwargs):
        """Initialize the form with an optional device scope.

        Args:
            device: an optional NetBox ``dcim.Device`` to scope snapshot
                lookups by in ``clean()`` (defence-in-depth: the view also
                re-validates ``device=device``). When ``None``, the form
                falls back to an unscoped pk lookup (back-compat with
                callers/tests that do not pass a device).
        """
        super().__init__(*args, **kwargs)
        self.device = device

    def clean(self):
        super().clean()
        before_id = self.cleaned_data.get("before_id")
        after_id = self.cleaned_data.get("after_id")
        if before_id is None or after_id is None:
            return self.cleaned_data

        qs = PyatsSnapshot.objects.all()
        if self.device is not None:
            qs = qs.filter(device=self.device)
        before = qs.filter(pk=before_id).only("kind").first()
        after = qs.filter(pk=after_id).only("kind").first()
        if before is None or after is None:
            raise forms.ValidationError("Both snapshots must exist. " f"(before_id={before_id}, after_id={after_id})")
        if before.kind != after.kind:
            raise forms.ValidationError(
                f"Snapshots must be the same kind to diff "
                f"(before is '{before.get_kind_display()}', "
                f"after is '{after.get_kind_display()}')."
            )
        return self.cleaned_data


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


# --------------------------------------------------------------------------- #
# Compliance forms (Phase 4, ATW-15)
# --------------------------------------------------------------------------- #


class PyatsGoldenConfigForm(NetBoxModelForm):
    """Create/edit form for a PyATS Golden Config (Phase 4, ATW-15).

    The operator types/pastes the golden ``config_text`` directly, or — via the
    "promote from snapshot" flow — the form is pre-filled from a snapshot's
    parsed config. ``source`` records provenance (manual vs. snapshot); the
    ``source_snapshot`` FK is only set when promoting from a snapshot.
    """

    # ``config_text`` is a running-config body, not a one-line label: trailing
    # newlines and indentation are semantically meaningful (Genie's config
    # parser groups indented lines under `!`-delimited section headers). The
    # default CharField strips leading/trailing whitespace, which would silently
    # corrupt pasted configs — so override with strip=False and a Textarea.
    config_text = forms.CharField(
        required=False,
        strip=False,
        widget=forms.Textarea(attrs={"rows": 20, "class": "font-monospace"}),
        help_text=(
            "Golden running-config text (the 'expected' device config). "
            "Diffed against a snapshot's parsed config payload by the "
            "compliance pipeline. May be empty only for a placeholder golden; "
            "compliance runs against an empty golden classify as 'error'."
        ),
    )

    fieldsets = (
        FieldSet("name", "device", "source", "source_snapshot", name="Golden Config"),
        FieldSet("config_text", name="Config text"),
        FieldSet("tags", name="Tags"),
    )

    class Meta:
        model = PyatsGoldenConfig
        fields = (
            "name",
            "device",
            "config_text",
            "source",
            "source_snapshot",
            "tags",
        )


class PyatsGoldenConfigFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsGoldenConfig list view."""

    model = PyatsGoldenConfig

    q = forms.CharField(required=False, label="Search")
    device = forms.IntegerField(required=False, label="Device ID")
    source = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + GoldenConfigSourceChoices.choices,
    )


class DeviceComplianceForm(forms.Form):
    """Form backing the device-page "Run compliance" picker (Phase 4).

    Posted to the ``device_compliance`` view. The operator selects a golden
    config and a snapshot of the same device, and a comparison mode; the view
    enqueues :func:`jobs.enqueue_compliance`. The device is in the URL;
    ``golden_id`` and ``snapshot_id`` are validated by the view to belong to
    that device.

    ``mode`` selects the comparison semantics (ATW-434): ``ordered`` (v2,
    default) is a sequence-aware line diff that flags re-ordered ACL/route-map
    /interface lines as drift; ``set`` (v1) is an order-independent set diff
    that classifies a re-ordered config as compliant. The default is
    ``ordered`` so the operator gets the more informative comparison unless
    they explicitly opt into the v1 semantics.
    """

    golden_id = forms.IntegerField(required=True, label="Golden config")
    snapshot_id = forms.IntegerField(required=True, label="Snapshot")
    mode = forms.ChoiceField(
        required=False,
        choices=ComplianceModeChoices.choices,
        initial=ComplianceModeChoices.MODE_ORDERED,
        label="Mode",
        help_text=(
            "Ordered (v2, default) flags re-ordered lines as drift; Set (v1) "
            "treats a re-ordered config as compliant."
        ),
    )


class PyatsComplianceRunFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsComplianceRun list view."""

    model = PyatsComplianceRun

    q = forms.CharField(required=False, label="Search")
    device = forms.IntegerField(required=False, label="Device ID")
    result = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + ComplianceResultChoices.choices,
    )
    mode = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + ComplianceModeChoices.choices,
    )
    has_drift = forms.BooleanField(required=False, label="Only runs with drift")
    has_warnings = forms.BooleanField(required=False, label="Only runs with warnings")


# --------------------------------------------------------------------------- #
# PyatsJob forms (Phase 5, ATW-16)
# --------------------------------------------------------------------------- #


class PyatsJobFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsJob list view (Phase 5, ATW-16).

    Jobs are append-only history (ADR-0005 §4): no edit form, standard delete
    only. The filter form exposes the axes the unified jobs view is filterable
    on: job_type (capture / diff / compliance / batch_capture), status
    (pending / running / success / error / partial), and device.
    """

    model = PyatsJob

    q = forms.CharField(required=False, label="Search")
    device = forms.IntegerField(required=False, label="Device ID")
    job_type = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + PyatsJobTypeChoices.choices,
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + PyatsJobStatusChoices.choices,
    )


class DeviceBulkCaptureForm(forms.Form):
    """Form backing the device-list bulk "PyATS capture" action (Phase 5, ATW-16).

    Posted to the :class:`DeviceBulkCaptureView` from the NetBox device list
    when the operator selects a set of devices and chooses the "PyATS capture"
    bulk action. Only the capture ``kind`` is user-selectable; the device set
    is passed in the URL/form by NetBox's bulk-action machinery (the selected
    pks). The view enqueues :func:`jobs.enqueue_batch_capture`.
    """

    kind = forms.ChoiceField(
        choices=SnapshotKindChoices.choices,
        initial=SnapshotKindChoices.KIND_FULL,
        required=True,
        label="Capture kind",
    )


# --------------------------------------------------------------------------- #
# Device parse form (ATW-241 child 2, ATW-250)
# --------------------------------------------------------------------------- #


class DeviceParseForm(forms.Form):
    """Form backing the device-page "Parse" sub-tab (ATW-241 child 2, ATW-250).

    Posted to the :class:`DeviceParseView`. The operator may check one or more
    commands from the cached parser catalog (populated by the worker-only
    ``refresh_parser_catalog`` job — ATW-249) AND/OR type a free-text
    ``manual_command``; both inputs are accepted in the same submission. Each
    selected/typed command becomes one entry in the parse job's command list.
    The view resolves the device's pyATS os from
    :func:`netbox_pyats.testbed.platform_to_pyats_os` and passes it to the
    form constructor so ``__init__`` can populate ``commands`` choices from the
    catalog row for that os.

    No Genie import happens in the form (or the web process at all —
    ADR-0001 §6): the catalog is read from the DB only.
    """

    commands = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Parser commands",
        help_text=(
            "Cached list of CLI commands Genie can parse for this device's "
            "os, as reported by the worker's genie.libs.parser.utils."
            "get_parser_commands. Refresh the catalog after a genie.libs "
            "upgrade."
        ),
    )
    manual_command = forms.CharField(
        required=False,
        strip=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "font-monospace"}),
        label="Manual command",
        help_text=(
            "Optional free-text CLI command to parse. Useful when the command "
            "is not in the cached catalog or you want a one-off parse. May be "
            "submitted together with checkbox selections."
        ),
    )

    def __init__(self, *args, command_choices=None, **kwargs):
        """Initialize the form, optionally pinning the ``commands`` choices.

        Args:
            command_choices: an iterable of ``(value, label)`` tuples for the
                ``commands`` MultipleChoiceField. The view passes the catalog
                row's command list so the rendered checkboxes reflect the
                worker-populated catalog. When ``None`` (e.g. an unbound GET
                with no catalog row), the field has no choices — the manual
                text box still works.
        """
        super().__init__(*args, **kwargs)
        if command_choices is not None:
            self.fields["commands"].choices = list(command_choices)

    def clean(self):
        """Require at least one of ``commands`` or ``manual_command``.

        The parse job takes a non-empty command list; an empty submission has
        nothing to run. Raises :class:`django.core.exceptions.ValidationError`
        so the view re-renders the form with the error rather than enqueueing
        an empty job.
        """
        super().clean()
        commands = self.cleaned_data.get("commands") or []
        manual_command = (self.cleaned_data.get("manual_command") or "").strip()
        if not commands and not manual_command:
            raise forms.ValidationError("Select at least one parser command or type a manual command.")
        return self.cleaned_data


# --------------------------------------------------------------------------- #
# Capture schedule forms (ATW-433, ADR-0008)
# --------------------------------------------------------------------------- #


class PyatsCaptureScheduleForm(NetBoxModelForm):
    """Create/edit form for a PyATS Capture Schedule (ATW-433).

    The operator enters a ``device_filter`` as a JSON ORM lookup spec (e.g.
    ``{"site__region_id__in": [1, 2]}`` or ``{"id__in": [10, 20]}``). The field
    is a ``JSONField`` rendered as a textarea; the dispatcher re-resolves it to
    a Device queryset at run time. The ``kind`` reuses
    :class:`SnapshotKindChoices` (no new choice values).
    """

    device_filter = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6, "class": "font-monospace"}),
        help_text=(
            'JSON ORM filter spec (e.g. {"site__region_id__in": [1, 2]} or '
            '{"id__in": [10, 20]}). Re-resolved to a Device queryset at run '
            "time. Leave empty to match no devices."
        ),
    )

    fieldsets = (
        FieldSet("name", "kind", "enabled", "device_filter", name="Schedule"),
        FieldSet("tags", name="Tags"),
    )

    class Meta:
        model = PyatsCaptureSchedule
        fields = (
            "name",
            "kind",
            "enabled",
            "device_filter",
            "tags",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate the JSON textarea with the stored spec as a pretty
        # JSON string so the operator sees the current filter on edit.
        if self.instance and self.instance.pk and self.instance.device_filter:
            import json

            self.fields["device_filter"].initial = json.dumps(self.instance.device_filter, indent=2)

    # Allowed top-level and one-hop relationship keys for the device_filter JSON
    # field. Extending this set requires CTO sign-off since it broadens the
    # ORM surface an operator can query against (ATW-578).
    DEVICE_FILTER_ALLOWED_KEYS = frozenset(
        {
            # Direct device fields
            "id",
            "id__in",
            "id__not_in",
            "name",
            "name__icontains",
            "name__startswith",
            "name__endswith",
            "name__iexact",
            "status",
            "status__in",
            "status__not_in",
            "serial",
            # Site
            "site_id",
            "site",
            "site__slug",
            "site__slug__in",
            "site__name",
            "site__name__icontains",
            # Region (Device has no direct region FK in NetBox 4.6; reach via site)
            "site__region_id",
            "site__region",
            "site__region__slug",
            "site__region__slug__in",
            "site__region__name",
            "site__region__name__icontains",
            # Tenant
            "tenant_id",
            "tenant",
            "tenant__slug",
            "tenant__slug__in",
            "tenant__name",
            "tenant__name__icontains",
            # Device role (field is `role` on the NetBox 4.6 Device model)
            "role_id",
            "role",
            "role__slug",
            "role__slug__in",
            "role__name",
            "role__name__icontains",
            # Platform
            "platform_id",
            "platform",
            "platform__slug",
            "platform__slug__in",
            "platform__name",
            "platform__name__icontains",
            # Tags
            "tags",
            "tagged_items__tag__slug",
            "tagged_items__tag__slug__in",
        }
    )

    def clean_device_filter(self):
        """Parse the ``device_filter`` textarea to a dict (empty on blank).

        The field is a ``CharField`` on the form so the operator types JSON;
        the model stores a ``JSONField``. A blank submission yields an empty
        dict (matches the model default). An invalid JSON string raises a
        validation error so the form re-renders rather than crashing at save.

        Keys are validated against an allowlist to prevent operators from
        using arbitrary relationship traversals or JSON field access
        (ATW-578).
        """
        import json

        raw = (self.cleaned_data.get("device_filter") or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"device_filter must be valid JSON: {exc}")
        if not isinstance(parsed, dict):
            raise forms.ValidationError('device_filter must be a JSON object (e.g. {"id__in": [1, 2]}).')
        disallowed = set(parsed.keys()) - self.DEVICE_FILTER_ALLOWED_KEYS
        if disallowed:
            raise forms.ValidationError(
                f"device_filter contains disallowed keys: {sorted(disallowed)!r}. "
                f"Allowed keys: {sorted(self.DEVICE_FILTER_ALLOWED_KEYS)!r}."
            )
        return parsed


class PyatsCaptureScheduleFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsCaptureSchedule list view (ATW-433)."""

    model = PyatsCaptureSchedule

    q = forms.CharField(required=False, label="Search")
    kind = forms.ChoiceField(
        required=False,
        choices=[("", "---------")] + SnapshotKindChoices.choices,
    )
    enabled = forms.NullBooleanField(required=False, label="Enabled")


class PyatsParserCatalogRefreshScheduleForm(NetBoxModelForm):
    """Create/edit form for the PyatsParserCatalogRefreshSchedule (ATW-581).

    The model is a single-row intent gate for the recurring parser catalog
    refresh. The only operator-editable field is ``enabled`` (and tags);
    ``last_run_at`` / ``next_run_at`` are display-only, written by the
    dispatcher job. The form is kept minimal — there is no cadence field here
    because the cadence is owned by the NetBox ``Job`` row's ``interval``
    (set when the operator enqueues ``RunParserCatalogRefreshSchedulesJob``
    via the NetBox shell; see docs/user/scheduled-parser-catalog-refresh.md).
    """

    fieldsets = (
        FieldSet("enabled", name="Refresh Schedule"),
        FieldSet("tags", name="Tags"),
    )

    class Meta:
        model = PyatsParserCatalogRefreshSchedule
        fields = ("enabled", "tags")


class PyatsParserCatalogRefreshScheduleFilterForm(NetBoxModelFilterSetForm):
    """Filter form for the PyatsParserCatalogRefreshSchedule list view (ATW-581)."""

    model = PyatsParserCatalogRefreshSchedule

    q = forms.CharField(required=False, label="Search")
    enabled = forms.NullBooleanField(required=False, label="Enabled")

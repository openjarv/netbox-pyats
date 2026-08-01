from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_pyats.models import (
    PyatsCaptureSchedule,
    PyatsComplianceRun,
    PyatsCredential,
    PyatsGoldenConfig,
    PyatsJob,
    PyatsParserCatalog,
    PyatsSnapshot,
    PyatsSnapshotDiff,
)


class PyatsCredentialSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsCredential model.

    The ``password`` and ``enable_secret`` fields are ciphertext and are NOT
    exposed through the REST API. To set them, clients send
    ``plaintext_password`` / ``plaintext_enable_secret``; the serializer
    encrypts via the model setters, exactly like the form. Reading a credential
    never returns the secret — only the fact that one is set (the list/detail
    responses simply omit the ciphertext fields).
    """

    plaintext_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
    )
    plaintext_enable_secret = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = PyatsCredential
        fields = [
            "id",
            "url",
            "name",
            "scope",
            "device",
            "username",
            "protocol",
            "ssh_port",
            "tags",
            "created",
            "last_updated",
            # Write-only secrets — never returned.
            "plaintext_password",
            "plaintext_enable_secret",
        ]
        read_only_fields = ("id", "url", "created", "last_updated")

    # Non-model write-only fields that NetBoxModelSerializer.validate would
    # otherwise pass straight into ``Meta.model(**attrs)`` (raising TypeError
    # under NetBox 4.6, which stricter-instantiates the model during clean()).
    # Pop them before delegating to super().validate(), then re-attach so
    # create()/update() can consume them.
    _write_only_secret_fields = ("plaintext_password", "plaintext_enable_secret")

    def validate(self, data):
        secrets = {f: data.pop(f) for f in self._write_only_secret_fields if f in data}
        data = super().validate(data)
        data.update(secrets)
        return data

    def create(self, validated_data):
        plaintext_password = validated_data.pop("plaintext_password", "")
        plaintext_enable_secret = validated_data.pop("plaintext_enable_secret", "")
        instance = super().create(validated_data)
        if plaintext_password:
            instance.set_password(plaintext_password)
        if plaintext_enable_secret:
            instance.set_enable_secret(plaintext_enable_secret)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        plaintext_password = validated_data.pop("plaintext_password", "")
        plaintext_enable_secret = validated_data.pop("plaintext_enable_secret", "")
        instance = super().update(instance, validated_data)
        if plaintext_password:
            instance.set_password(plaintext_password)
        if plaintext_enable_secret:
            instance.set_enable_secret(plaintext_enable_secret)
        instance.save()
        return instance


class PyatsSnapshotSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsSnapshot model.

    Snapshots are read-only via the REST API in v1 — they are produced by the
    ``capture_snapshot`` RQ job, not by direct API writes. The full JSONB
    ``data`` payload is returned (it is the snapshot), along with
    ``parser_warnings``, the worker version strings, and ``size_bytes``.
    """

    class Meta:
        model = PyatsSnapshot
        fields = [
            "id",
            "url",
            "device",
            "kind",
            "status",
            "triggered_by",
            "captured_at",
            "data",
            "parser_warnings",
            "genie_version",
            "pyats_version",
            "size_bytes",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = (
            "id",
            "url",
            "captured_at",
            "data",
            "parser_warnings",
            "genie_version",
            "pyats_version",
            "size_bytes",
            "created",
            "last_updated",
        )


class PyatsSnapshotDiffSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsSnapshotDiff model.

    Diffs are read-only via the REST API in v1 — they are produced by the
    ``run_diff`` RQ job, not by direct API writes. The full JSONB ``diff``
    tree and ``summary`` are returned (they are the diff), along with
    ``parser_warnings`` and ``size_bytes``.
    """

    class Meta:
        model = PyatsSnapshotDiff
        fields = [
            "id",
            "url",
            "device",
            "before",
            "after",
            "status",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = (
            "id",
            "url",
            "status",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "created",
            "last_updated",
        )


class PyatsGoldenConfigSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsGoldenConfig model (Phase 4, ATW-15).

    Golden configs are fully editable via the REST API in v1 — an operator
    can create/update/delete a golden config (e.g. to seed it from an external
    config-management tool) and then run compliance against it from the
    device page. The full ``config_text`` body is returned (it is the golden).
    """

    # ``config_text`` is a running-config body, not a one-line label: trailing
    # newlines and indentation are semantically meaningful (Genie's config
    # parser groups indented lines under `!`-delimited section headers). DRF's
    # CharField.strip defaults to True, which would silently strip a trailing
    # newline from a pasted config — so override with strip=False to preserve
    # the golden exactly as submitted.
    config_text = serializers.CharField(
        allow_blank=True,
        trim_whitespace=False,
        style={"base_template": "textarea.html", "rows": 20},
    )

    class Meta:
        model = PyatsGoldenConfig
        fields = [
            "id",
            "url",
            "device",
            "name",
            "config_text",
            "source",
            "source_snapshot",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = ("id", "url", "created", "last_updated")


class PyatsComplianceRunSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsComplianceRun model (Phase 4, ATW-15).

    Compliance runs are read-only via the REST API in v1 — they are produced
    by the ``run_compliance`` RQ job, not by direct API writes. The full JSONB
    ``diff`` tree and ``summary`` are returned (they are the compliance result),
    along with ``parser_warnings`` and ``size_bytes``.
    """

    class Meta:
        model = PyatsComplianceRun
        fields = [
            "id",
            "url",
            "device",
            "golden",
            "snapshot",
            "result",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = (
            "id",
            "url",
            "result",
            "diff",
            "summary",
            "parser_warnings",
            "size_bytes",
            "created",
            "last_updated",
        )


class PyatsJobSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsJob model (Phase 5, ATW-16).

    Jobs are read-only via the REST API in v1 (ADR-0005 §4) — they are produced
    by the plugin's ``enqueue_*`` helpers, not by direct API writes. The full
    row is returned, including the ``error`` text (populated only when the
    result row could not be written) and the batch ``summary`` counts (for
    batch_capture jobs). The ``related_snapshot`` / ``related_diff`` /
    ``related_compliance`` FKs are exposed so API clients can drill from a job
    to the result row it produced.
    """

    class Meta:
        model = PyatsJob
        fields = [
            "id",
            "url",
            "job_type",
            "status",
            "device",
            "core_job",
            "rq_job_id",
            "related_snapshot",
            "related_diff",
            "related_compliance",
            "started_at",
            "finished_at",
            "error",
            "summary",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = (
            "id",
            "url",
            "job_type",
            "status",
            "device",
            "core_job",
            "rq_job_id",
            "related_snapshot",
            "related_diff",
            "related_compliance",
            "started_at",
            "finished_at",
            "error",
            "summary",
            "created",
            "last_updated",
        )


class PyatsParserCatalogSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsParserCatalog model (ATW-241 child 1, ATW-249).

    Read-only via the REST API in v1 (ADR-0001 §5): the catalog is populated
    by the worker-only ``refresh_parser_catalog`` RQ job, not by direct API
    writes. The full ``commands`` JSONB list is returned (it is the catalog),
    along with the worker version strings and ``refreshed_at``.
    """

    class Meta:
        model = PyatsParserCatalog
        fields = [
            "id",
            "url",
            "pyats_os",
            "commands",
            "genie_version",
            "pyats_version",
            "refreshed_at",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = (
            "id",
            "url",
            "pyats_os",
            "commands",
            "genie_version",
            "pyats_version",
            "refreshed_at",
            "created",
            "last_updated",
        )


class PyatsCaptureScheduleSerializer(NetBoxModelSerializer):
    """Serializer for the PyatsCaptureSchedule model (ATW-433).

    Fully editable via the REST API in v1 (operators can create/update/delete
    schedules, e.g. to seed them from an external config-management tool).
    The ``device_filter`` JSONField is returned as-is (it is the filter spec).
    ``last_run_at`` / ``next_run_at`` are written by the dispatcher job, so
    they are read-only on the API.
    """

    class Meta:
        model = PyatsCaptureSchedule
        fields = [
            "id",
            "url",
            "name",
            "device_filter",
            "kind",
            "enabled",
            "last_run_at",
            "next_run_at",
            "tags",
            "created",
            "last_updated",
        ]
        read_only_fields = ("id", "url", "last_run_at", "next_run_at", "created", "last_updated")

from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_pyats.models import PyatsComplianceRun, PyatsCredential, PyatsGoldenConfig, PyatsSnapshot, PyatsSnapshotDiff


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

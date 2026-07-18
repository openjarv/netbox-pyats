from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from netbox_pyats.models import PyatsCredential, PyatsSnapshot


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

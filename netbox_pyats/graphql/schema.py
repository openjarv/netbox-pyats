from netbox.graphql.types import NetBoxObjectType

from netbox_pyats.models import PyatsCredential


class PyatsCredentialType(NetBoxObjectType):
    """GraphQL type for the PyatsCredential model.

    ``password`` and ``enable_secret`` ciphertext fields are excluded from the
    GraphQL schema entirely — secrets are never readable via GraphQL, only
    set via REST/UI.
    """

    class Meta:
        model = PyatsCredential
        fields = (
            "id",
            "name",
            "scope",
            "device",
            "username",
            "protocol",
            "ssh_port",
            "tags",
            "created",
            "last_updated",
        )


class Query:
    pass

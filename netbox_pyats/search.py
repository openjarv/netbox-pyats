"""Search index registration for the netbox_pyats plugin.

Registered only when NetBox is installed; otherwise this module is inert so
the pure-Python test suite can import the package.
"""

try:
    from netbox.search import SearchIndex, register_search
except ModuleNotFoundError:  # pragma: no cover - importable without netbox
    SearchIndex = None  # type: ignore[assignment]

    def register_search(cls):  # type: ignore[misc]
        return cls


if SearchIndex is not None:
    from .models import PyatsCredential  # noqa: E402

    @register_search
    class PyatsCredentialIndex(SearchIndex):
        model = PyatsCredential
        fields = (
            ("name", 100),
            ("username", 200),
        )

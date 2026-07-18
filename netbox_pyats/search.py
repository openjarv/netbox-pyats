from netbox.search import SearchIndex, register_search

from .models import PyatsCredential


@register_search
class PyatsCredentialIndex(SearchIndex):
    model = PyatsCredential
    fields = (
        ("name", 100),
        ("username", 200),
    )

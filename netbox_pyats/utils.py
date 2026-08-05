"""Shared helpers for the netbox_pyats plugin.

Single-purpose utility functions used by more than one layer (form, serializer,
model) live here so both the UI and REST API enforce identical rules. Import
only the helper you need — keep this module small and free of side effects.
"""

from __future__ import annotations

from collections.abc import Mapping

# Allowed top-level and one-hop relationship keys for a
# ``PyatsCaptureSchedule.device_filter`` JSON spec. Extending this set requires
# CTO sign-off since it broadens the ORM surface an operator can query against
# (ATW-578). Shared by the form and the serializer so the UI and REST API
# enforce the same allowlist (ATW-632).
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


def validate_device_filter_spec(parsed):
    """Validate a parsed ``device_filter`` spec dict against the allowlist.

    Args:
        parsed: the already-parsed dict from a ``device_filter`` JSONField /
            textarea. ``None`` or an empty value is treated as the empty dict.

    Returns:
        The validated dict (empty dict when ``parsed`` is falsy/empty).

    Raises:
        ValueError: when ``parsed`` is not a mapping or contains keys outside
            :data:`DEVICE_FILTER_ALLOWED_KEYS`. The caller (form or serializer)
            translates this into the appropriate framework error type
            (``django.forms.ValidationError`` / DRF ``ValidationError``) so the
            helper stays framework-agnostic and importable from either layer
            without pulling in form/DRF dependencies.
    """
    if not parsed:
        return {}
    if not isinstance(parsed, Mapping):
        raise ValueError('device_filter must be a JSON object (e.g. {"id__in": [1, 2]}).')
    disallowed = set(parsed.keys()) - DEVICE_FILTER_ALLOWED_KEYS
    if disallowed:
        raise ValueError(
            f"device_filter contains disallowed keys: {sorted(disallowed)!r}. "
            f"Allowed keys: {sorted(DEVICE_FILTER_ALLOWED_KEYS)!r}."
        )
    return dict(parsed)

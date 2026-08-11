"""Worker status helper for the pyATS RQ queue (ATW-804).

A pure-Python, resilient helper that reports whether at least one RQ worker
is listening on the dedicated ``pyats`` queue. The result is surfaced in the
plugin UI as a red/green badge so operators see the worker state *before*
triggering a Capture/Diff/Compliance/Parse/Learn job — instead of clicking a
button that silently enqueues a job that sits on the queue forever.

Design constraints (ADR-0001 §4/§6 — no JS, no Genie in the web process):

- **NetBox/RQ-optional at import time.** The module is importable without
  NetBox/RQ/Redis installed (same pattern as ``jobs.py`` / ``capture.py``).
  All ``rq`` / ``django_rq`` / Redis imports are lazy, inside the function
  body, guarded by try/except. This keeps the pure-Python unit test lane
  clean.
- **Never raises.** This is a UI indicator, not a gate. If Redis is
  unreachable, the queue does not exist, or RQ is not installed, return
  ``online=False`` with a short human-readable reason string.
- **Cheap.** One Redis ping + one ``Worker.count`` call per page render. The
  result is cached in the Django cache for a short TTL so a high-traffic
  device tab does not hit Redis on every render.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Cache TTL for the worker-status result. Short enough to reflect a worker
#: being started/stopped within ~15s, long enough to absorb rapid tab renders.
_WORKER_STATUS_TTL = 15

#: Cache key (single slot — one status for the whole ``pyats`` queue).
_WORKER_STATUS_CACHE_KEY = "netbox_pyats:worker_status"


def get_worker_status() -> tuple[bool, str]:
    """Return ``(online, reason)`` for the dedicated ``pyats`` RQ queue.

    ``online=True`` when at least one RQ worker is registered on the
    ``pyats`` queue. ``reason`` is a short human-readable label for the
    badge tooltip (e.g. ``"1 worker on pyats"``, ``"no workers on pyats
    queue"``, ``"redis unreachable"``).

    Never raises — any failure (RQ missing, Redis unreachable, queue absent)
    degrades to ``online=False`` with a descriptive reason. The result is
    cached in the Django cache for :data:`_WORKER_STATUS_TTL` seconds when a
    cache backend is available; in pure-Python mode (no Django cache) the
    check runs each call.
    """
    cache = _get_cache()
    if cache is not None:
        cached = cache.get(_WORKER_STATUS_CACHE_KEY)
        if cached is not None:
            return cached

    result = _check_worker_status()
    if cache is not None:
        try:
            cache.set(_WORKER_STATUS_CACHE_KEY, result, _WORKER_STATUS_TTL)
        except Exception:
            logger.debug("worker_status: cache set failed", exc_info=True)
    return result


def _check_worker_status() -> tuple[bool, str]:
    """Run the actual RQ/Redis worker check (uncached).

    Kept separate from :func:`get_worker_status` so the cache layer wraps a
    single cheap call.
    """
    try:
        import django_rq  # type: ignore[import-not-found]
        import rq  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return False, "RQ not installed"

    from .jobs import PYATS_QUEUE

    try:
        connection = django_rq.get_connection(PYATS_QUEUE)
        # Cheap liveness check — fail fast if Redis is down.
        connection.ping()
    except Exception as exc:
        logger.debug("worker_status: redis unreachable (%s)", exc)
        return False, "redis unreachable"

    try:
        count = rq.Worker.count(connection=connection, queue=PYATS_QUEUE)
    except Exception as exc:
        logger.debug("worker_status: Worker.count failed (%s)", exc)
        return False, "worker check failed"

    if count and count > 0:
        return True, f"{count} worker{'s' if count != 1 else ''} on {PYATS_QUEUE}"
    return False, f"no workers on {PYATS_QUEUE} queue"


def _get_cache():
    """Return the Django cache backend or ``None`` when unavailable.

    Pure-Python mode (no Django settings configured, or no cache backend)
    returns ``None`` — callers fall back to running the check each time.
    """
    try:
        from django.core.cache import cache  # type: ignore[import-not-found]
    except Exception:
        return None

    try:
        # Touch the backend so a misconfigured/missing cache is detected here
        # rather than mid-set; ``cache`` is a module-level proxy that resolves
        # on first attribute access.
        cache.get  # noqa: B018
    except Exception:
        return None
    return cache

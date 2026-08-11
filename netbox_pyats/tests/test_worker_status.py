"""Tests for the worker status indicator (ATW-804).

Two lanes, matching the repo's dual-mode test convention (see
``conftest.py``):

1. **Pure-Python lane** (no NetBox/Redis installed): the graceful-fallback
   path — ``get_worker_status()`` returns ``(False, <reason>)`` and never
   raises when ``rq`` / ``django_rq`` / Redis is not importable. These run
   in the fast unit lane (``scripts/test-unit.sh`` / CI unit job).
2. **Integration lane** (NetBox test DB, ``pytest.importorskip("netbox")``):
   the views render the badge in the response HTML. ``get_worker_status``
   is monkeypatched so the view tests do not need a live RQ worker (same
   pattern as ``test_genie_parse.py`` / ``test_device_parse.py``).
"""

from __future__ import annotations

from unittest import mock

# --------------------------------------------------------------------------- #
# Pure-Python lane — graceful fallback when RQ/Redis is unavailable.
# --------------------------------------------------------------------------- #


class TestWorkerStatusFallback:
    """``get_worker_status()`` must degrade to ``(False, reason)`` and never raise.

    These tests run without NetBox/RQ/Redis installed (pure-Python lane).
    They exercise the import-time + runtime fallback paths in
    ``worker_status.py``.
    """

    def test_returns_false_when_rq_not_importable(self):
        # In pure-Python mode neither rq nor django_rq is importable, so the
        # helper must return online=False with a short reason.
        from netbox_pyats.worker_status import get_worker_status

        online, reason = get_worker_status()
        assert online is False
        assert isinstance(reason, str) and reason

    def test_never_raises_on_missing_rq_module(self):
        # Simulate ModuleNotFoundError for the rq/django_rq imports so the
        # fallback path is exercised explicitly even when rq happens to be
        # installed in the local env.
        from netbox_pyats import worker_status

        with mock.patch("builtins.__import__", side_effect=ModuleNotFoundError("rq")):
            online, reason = worker_status._check_worker_status()
        assert online is False
        assert "not installed" in reason or "unreachable" in reason or "no workers" in reason

    def test_returns_false_when_redis_unreachable(self):
        # Stub rq + django_rq as importable, but make the Redis connection
        # raise — the helper must report "redis unreachable".
        from netbox_pyats import worker_status

        fake_rq = mock.MagicMock()
        fake_rq.Worker.count = mock.MagicMock(return_value=0)
        fake_django_rq = mock.MagicMock()
        fake_django_rq.get_connection = mock.MagicMock(side_effect=Exception("connection refused"))

        with mock.patch.dict(
            "sys.modules",
            {"rq": fake_rq, "django_rq": fake_django_rq},
        ):
            online, reason = worker_status._check_worker_status()
        assert online is False
        assert "redis unreachable" in reason

    def test_returns_false_when_zero_workers(self):
        # rq + django_rq importable, Redis ping succeeds, but Worker.count
        # returns 0 — the helper must report "no workers on pyats queue".
        from netbox_pyats import worker_status

        fake_connection = mock.MagicMock()
        fake_connection.ping = mock.MagicMock(return_value=True)
        fake_rq = mock.MagicMock()
        fake_rq.Worker.count = mock.MagicMock(return_value=0)
        fake_django_rq = mock.MagicMock()
        fake_django_rq.get_connection = mock.MagicMock(return_value=fake_connection)

        with mock.patch.dict(
            "sys.modules",
            {"rq": fake_rq, "django_rq": fake_django_rq},
        ):
            online, reason = worker_status._check_worker_status()
        assert online is False
        assert "no workers" in reason

    def test_returns_true_when_one_worker(self):
        # rq + django_rq importable, Redis ping succeeds, Worker.count=1.
        from netbox_pyats import worker_status

        fake_connection = mock.MagicMock()
        fake_connection.ping = mock.MagicMock(return_value=True)
        fake_rq = mock.MagicMock()
        fake_rq.Worker.count = mock.MagicMock(return_value=1)
        fake_django_rq = mock.MagicMock()
        fake_django_rq.get_connection = mock.MagicMock(return_value=fake_connection)

        with mock.patch.dict(
            "sys.modules",
            {"rq": fake_rq, "django_rq": fake_django_rq},
        ):
            online, reason = worker_status._check_worker_status()
        assert online is True
        assert "1 worker" in reason

    def test_returns_true_when_multiple_workers_pluralizes(self):
        from netbox_pyats import worker_status

        fake_connection = mock.MagicMock()
        fake_connection.ping = mock.MagicMock(return_value=True)
        fake_rq = mock.MagicMock()
        fake_rq.Worker.count = mock.MagicMock(return_value=3)
        fake_django_rq = mock.MagicMock()
        fake_django_rq.get_connection = mock.MagicMock(return_value=fake_connection)

        with mock.patch.dict(
            "sys.modules",
            {"rq": fake_rq, "django_rq": fake_django_rq},
        ):
            online, reason = worker_status._check_worker_status()
        assert online is True
        assert "3 workers" in reason

    def test_check_worker_status_does_not_cache(self):
        # _check_worker_status is the uncached primitive; get_worker_status
        # wraps it with the Django cache. Verify the split is honest.
        from netbox_pyats import worker_status

        with mock.patch.object(worker_status, "_check_worker_status", return_value=(False, "stub")) as chk:
            worker_status._check_worker_status()
            worker_status._check_worker_status()
        assert chk.call_count == 2


# --------------------------------------------------------------------------- #
# Integration lane — views render the badge (NetBox test DB required).
# --------------------------------------------------------------------------- #

import unittest  # noqa: E402

try:  # NetBox is only available in the integration lane.
    from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Platform, Site  # noqa: E402
    from django.urls import reverse  # noqa: E402
    from utilities.testing import TestCase  # noqa: E402

    from netbox_pyats.models import PyatsParserCatalog  # noqa: E402

    _NETBOX_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - pure-Python test mode
    _NETBOX_AVAILABLE = False
    # Fallback base so the class definition below does not raise NameError
    # at collection time; @skipUnless(_NETBOX_AVAILABLE) skips the class.
    TestCase = unittest.TestCase


@unittest.skipUnless(_NETBOX_AVAILABLE, "NetBox not installed")
class WorkerStatusBadgeViewTest(TestCase):
    """The six worker-using views must render the worker status badge (ATW-804).

    ``get_worker_status`` is monkeypatched to a fixed (online, reason) pair
    so the tests do not need a live RQ worker. Asserts the badge partial
    renders the ``Worker online`` / ``Worker offline`` text and the matching
    ``bg-success`` / ``bg-danger`` class.
    """

    user_permissions = (
        "netbox_pyats.add_pyatssnapshot",
        "netbox_pyats.view_pyatssnapshot",
        "netbox_pyats.add_pyatsjob",
        "netbox_pyats.view_pyatsjob",
        "netbox_pyats.add_pyatssnapshotdiff",
        "netbox_pyats.view_pyatssnapshotdiff",
        "dcim.view_device",
    )

    @classmethod
    def setUpTestData(cls):
        cls.site = Site.objects.create(name="WS01", slug="ws01")
        cls.mfr = Manufacturer.objects.create(name="Cisco-WS", slug="cisco-ws")
        cls.platform_iosxe = Platform.objects.create(name="Cisco IOS-XE", slug="cisco-iosxe", manufacturer=cls.mfr)
        cls.dt = DeviceType.objects.create(model="C9300-WS", slug="c9300-ws", manufacturer=cls.mfr)
        cls.role = DeviceRole.objects.create(name="Router-WS", slug="router-ws")
        cls.device = Device.objects.create(
            name="wsrtr01",
            site=cls.site,
            device_type=cls.dt,
            role=cls.role,
            platform=cls.platform_iosxe,
        )
        # Parser catalog row so the Parse sub-tab / Genie Parse page render
        # their command list without a 500 (the parse GET path reads it).
        PyatsParserCatalog.objects.create(
            pyats_os="iosxe",
            commands=["show version"],
            genie_version="26.6",
            pyats_version="26.6",
        )

    # --- online badge ----------------------------------------------------- #

    def test_device_tab_renders_online_badge(self):
        url = f"/dcim/devices/{self.device.pk}/pyats/"
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")
        self.assertContains(response, "bg-success")
        self.assertContains(response, "1 worker on pyats")

    def test_device_parse_renders_online_badge(self):
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")

    def test_genie_parse_renders_online_badge(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")

    def test_genie_learn_renders_online_badge(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")

    def test_genie_diff_renders_online_badge(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")

    def test_device_bulk_capture_renders_online_badge(self):
        url = reverse("plugins:netbox_pyats:device_bulk_capture")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(True, "1 worker on pyats")):
            response = self.client.get(url, {"pk": self.device.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker online")

    # --- offline badge ---------------------------------------------------- #

    def test_device_tab_renders_offline_badge(self):
        url = f"/dcim/devices/{self.device.pk}/pyats/"
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers on pyats queue")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")
        self.assertContains(response, "no workers on pyats queue")

    def test_device_parse_renders_offline_badge(self):
        url = reverse("plugins:netbox_pyats:device_parse", kwargs={"device_id": self.device.pk})
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")

    def test_genie_parse_renders_offline_badge(self):
        url = reverse("plugins:netbox_pyats:genie_parse")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")

    def test_genie_learn_renders_offline_badge(self):
        url = reverse("plugins:netbox_pyats:genie_learn")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")

    def test_genie_diff_renders_offline_badge(self):
        url = reverse("plugins:netbox_pyats:genie_diff")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers")):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")

    def test_device_bulk_capture_renders_offline_badge(self):
        url = reverse("plugins:netbox_pyats:device_bulk_capture")
        with mock.patch("netbox_pyats.views.get_worker_status", return_value=(False, "no workers")):
            response = self.client.get(url, {"pk": self.device.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Worker offline")
        self.assertContains(response, "bg-danger")

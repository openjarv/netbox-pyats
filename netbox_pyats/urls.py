from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_pyats import views

app_name = "netbox_pyats"

urlpatterns = [
    # PyATS Credentials (standard NetBox CRUD). Detail/Edit/Delete/Changelog/
    # Journal are auto-registered via register_model_view on the view classes
    # and wired in by get_model_urls. The list/add/bulk-delete paths are not
    # model-attached detail views, so they stay explicit.
    path("credentials/", views.PyatsCredentialListView.as_view(), name="pyatscredential_list"),
    path("credentials/add/", views.PyatsCredentialEditView.as_view(), name="pyatscredential_add"),
    path("credentials/delete/", views.PyatsCredentialBulkDeleteView.as_view(), name="pyatscredential_bulk_delete"),
    path("credentials/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatscredential"))),
    # PyATS Snapshots (Phase 2, ATW-13)
    path("snapshots/", views.PyatsSnapshotListView.as_view(), name="pyatssnapshot_list"),
    path("snapshots/delete/", views.PyatsSnapshotBulkDeleteView.as_view(), name="pyatssnapshot_bulk_delete"),
    path("snapshots/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatssnapshot"))),
    # PyATS Snapshot Diffs (Phase 3, ATW-14)
    path("diffs/", views.PyatsSnapshotDiffListView.as_view(), name="pyatssnapshotdiff_list"),
    path("diffs/delete/", views.PyatsSnapshotDiffBulkDeleteView.as_view(), name="pyatssnapshotdiff_bulk_delete"),
    path("diffs/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatssnapshotdiff"))),
    # PyATS Golden Configs (Phase 4, ATW-15)
    path(
        "golden-configs/",
        views.PyatsGoldenConfigListView.as_view(),
        name="pyatsgoldenconfig_list",
    ),
    path(
        "golden-configs/add/",
        views.PyatsGoldenConfigEditView.as_view(),
        name="pyatsgoldenconfig_add",
    ),
    path(
        "golden-configs/delete/",
        views.PyatsGoldenConfigBulkDeleteView.as_view(),
        name="pyatsgoldenconfig_bulk_delete",
    ),
    path("golden-configs/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatsgoldenconfig"))),
    # PyATS Compliance Runs (Phase 4, ATW-15)
    path(
        "compliance-runs/",
        views.PyatsComplianceRunListView.as_view(),
        name="pyatscompliancerun_list",
    ),
    path(
        "compliance-runs/delete/",
        views.PyatsComplianceRunBulkDeleteView.as_view(),
        name="pyatscompliancerun_bulk_delete",
    ),
    path("compliance-runs/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatscompliancerun"))),
    # PyATS Jobs (Phase 5, ATW-16) — unified jobs view + detail + bulk delete.
    # Jobs are append-only history (no add/edit); standard delete only.
    path("jobs/", views.PyatsJobListView.as_view(), name="pyatsjob_list"),
    path("jobs/delete/", views.PyatsJobBulkDeleteView.as_view(), name="pyatsjob_bulk_delete"),
    path("jobs/<int:pk>/", include(get_model_urls("netbox_pyats", "pyatsjob"))),
    # Supported-platforms report (Phase 5, ATW-16, Option A). Web-process-safe —
    # reads the static PLATFORM_SLUG_TO_PYATS_OS map; no Genie import.
    path(
        "supported-platforms/",
        views.SupportedPlatformsReportView.as_view(),
        name="supported_platforms",
    ),
    # Device-page endpoints (POST from the PyATS tab on a Device)
    path("devices/<int:device_id>/capture/", views.DeviceCaptureView.as_view(), name="device_capture"),
    path("devices/<int:device_id>/diff/", views.DeviceDiffView.as_view(), name="device_diff"),
    path(
        "devices/<int:device_id>/compliance/",
        views.DeviceComplianceView.as_view(),
        name="device_compliance",
    ),
    # Device-list bulk action (Phase 5, ATW-16). Wired under /devices/bulk-capture/
    # so NetBox's bulk-action machinery can route the device-list form POST here.
    path("devices/bulk-capture/", views.DeviceBulkCaptureView.as_view(), name="device_bulk_capture"),
]

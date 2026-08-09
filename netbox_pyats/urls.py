from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_pyats import views

app_name = "netbox_pyats"

urlpatterns = [
    # Genie dedicated pages (ATW-728 nav restructure → ATW-729 dedicated
    # Parse page). Parse now has a full first-class page (device picker +
    # parse form + recent results) superseding the interim redirect landing.
    # Learn remains on the interim landing page until ATW-730. Diff reuses
    # pyatssnapshotdiff_list.
    path("genie/parse/", views.GenieParseView.as_view(), name="genie_parse"),
    path("genie/learn/", views.GenieLearnLandingView.as_view(), name="genie_learn"),
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
    # Device-page Parse sub-tab (ATW-241 child 2, ATW-250). A GET form view + POST
    # enqueue (unlike the POST-only endpoints above — the operator needs to see
    # the cached parser command list and pick). Reads the PyatsParserCatalog
    # row from the DB only; enqueues the parse job on the pyats queue. No
    # Genie import in the web process (ADR-0001 §6).
    path("devices/<int:device_id>/parse/", views.DeviceParseView.as_view(), name="device_parse"),
    # "Refresh parser list" button on the parse sub-tab — enqueues the
    # worker-only catalog refresh job (ATW-249) and redirects back to the
    # parse page.
    path(
        "devices/<int:device_id>/refresh-parser-catalog/",
        views.DeviceRefreshCatalogView.as_view(),
        name="device_refresh_parser_catalog",
    ),
    # Capture schedules (ATW-433, ADR-0008) — operator-authored intent model
    # for recurring snapshot capture. Full CRUD (add/edit/delete/bulk-delete)
    # like the other operator-authored models. The cadence is owned by
    # NetBox's native Job interval (RunCaptureSchedulesJob, a JobRunner
    # subclass), auto-rescheduled by JobRunner.handle.
    path(
        "capture-schedules/",
        views.PyatsCaptureScheduleListView.as_view(),
        name="pyatscaptureschedule_list",
    ),
    path(
        "capture-schedules/add/",
        views.PyatsCaptureScheduleEditView.as_view(),
        name="pyatscaptureschedule_add",
    ),
    path(
        "capture-schedules/delete/",
        views.PyatsCaptureScheduleBulkDeleteView.as_view(),
        name="pyatscaptureschedule_bulk_delete",
    ),
    path(
        "capture-schedules/<int:pk>/",
        include(get_model_urls("netbox_pyats", "pyatscaptureschedule")),
    ),
    # Parser catalog refresh schedule (ATW-581) — single-row intent gate for
    # the recurring parser catalog refresh. Same CRUD shape as capture
    # schedules; the cadence is owned by NetBox's native Job interval
    # (RunParserCatalogRefreshSchedulesJob, a JobRunner subclass),
    # auto-rescheduled by JobRunner.handle.
    path(
        "parser-catalog-refresh-schedules/",
        views.PyatsParserCatalogRefreshScheduleListView.as_view(),
        name="pyatsparsercatalogrefreshschedule_list",
    ),
    path(
        "parser-catalog-refresh-schedules/add/",
        views.PyatsParserCatalogRefreshScheduleEditView.as_view(),
        name="pyatsparsercatalogrefreshschedule_add",
    ),
    path(
        "parser-catalog-refresh-schedules/delete/",
        views.PyatsParserCatalogRefreshScheduleBulkDeleteView.as_view(),
        name="pyatsparsercatalogrefreshschedule_bulk_delete",
    ),
    path(
        "parser-catalog-refresh-schedules/<int:pk>/",
        include(get_model_urls("netbox_pyats", "pyatsparsercatalogrefreshschedule")),
    ),
]

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
    # Device-page endpoints (POST from the PyATS tab on a Device)
    path("devices/<int:device_id>/capture/", views.DeviceCaptureView.as_view(), name="device_capture"),
    path("devices/<int:device_id>/diff/", views.DeviceDiffView.as_view(), name="device_diff"),
]
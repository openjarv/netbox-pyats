from django.urls import path

from netbox_pyats import views

app_name = "netbox_pyats"

urlpatterns = [
    # PyATS Credentials (standard NetBox CRUD)
    path("credentials/", views.PyatsCredentialListView.as_view(), name="pyatscredential_list"),
    path("credentials/add/", views.PyatsCredentialEditView.as_view(), name="pyatscredential_add"),
    path("credentials/<int:pk>/", views.PyatsCredentialView.as_view(), name="pyatscredential"),
    path("credentials/<int:pk>/edit/", views.PyatsCredentialEditView.as_view(), name="pyatscredential_edit"),
    path("credentials/<int:pk>/delete/", views.PyatsCredentialDeleteView.as_view(), name="pyatscredential_delete"),
    path("credentials/delete/", views.PyatsCredentialBulkDeleteView.as_view(), name="pyatscredential_bulk_delete"),
    # PyATS Snapshots (Phase 2, ATW-13)
    path("snapshots/", views.PyatsSnapshotListView.as_view(), name="pyatssnapshot_list"),
    path("snapshots/<int:pk>/", views.PyatsSnapshotView.as_view(), name="pyatssnapshot"),
    path("snapshots/<int:pk>/delete/", views.PyatsSnapshotDeleteView.as_view(), name="pyatssnapshot_delete"),
    path("snapshots/delete/", views.PyatsSnapshotBulkDeleteView.as_view(), name="pyatssnapshot_bulk_delete"),
    # PyATS Snapshot Diffs (Phase 3, ATW-14)
    path("diffs/", views.PyatsSnapshotDiffListView.as_view(), name="pyatssnapshotdiff_list"),
    path("diffs/<int:pk>/", views.PyatsSnapshotDiffView.as_view(), name="pyatssnapshotdiff"),
    path("diffs/<int:pk>/delete/", views.PyatsSnapshotDiffDeleteView.as_view(), name="pyatssnapshotdiff_delete"),
    path("diffs/delete/", views.PyatsSnapshotDiffBulkDeleteView.as_view(), name="pyatssnapshotdiff_bulk_delete"),
    # Device-page endpoints (POST from the PyATS tab on a Device)
    path("devices/<int:device_id>/capture/", views.DeviceCaptureView.as_view(), name="device_capture"),
    path("devices/<int:device_id>/diff/", views.DeviceDiffView.as_view(), name="device_diff"),
]

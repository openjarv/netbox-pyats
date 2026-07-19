from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("pyats-credentials", views.PyatsCredentialViewSet)
router.register("pyats-snapshots", views.PyatsSnapshotViewSet)
router.register("pyats-snapshot-diffs", views.PyatsSnapshotDiffViewSet)

app_name = "netbox_pyats"
urlpatterns = router.urls

from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("pyats-credentials", views.PyatsCredentialViewSet)
router.register("pyats-snapshots", views.PyatsSnapshotViewSet)
router.register("pyats-snapshot-diffs", views.PyatsSnapshotDiffViewSet)
router.register("pyats-golden-configs", views.PyatsGoldenConfigViewSet)
router.register("pyats-compliance-runs", views.PyatsComplianceRunViewSet)

app_name = "netbox_pyats"
urlpatterns = router.urls

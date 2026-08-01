from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("pyats-credentials", views.PyatsCredentialViewSet)
router.register("pyats-snapshots", views.PyatsSnapshotViewSet)
router.register("pyats-snapshot-diffs", views.PyatsSnapshotDiffViewSet)
router.register("pyats-golden-configs", views.PyatsGoldenConfigViewSet)
router.register("pyats-compliance-runs", views.PyatsComplianceRunViewSet)
router.register("pyats-jobs", views.PyatsJobViewSet)
router.register("pyats-parser-catalog", views.PyatsParserCatalogViewSet)
router.register("pyats-capture-schedules", views.PyatsCaptureScheduleViewSet)

app_name = "netbox_pyats"
urlpatterns = router.urls

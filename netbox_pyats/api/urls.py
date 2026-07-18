from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register("pyats-credentials", views.PyatsCredentialViewSet)

app_name = "netbox_pyats"
urlpatterns = router.urls

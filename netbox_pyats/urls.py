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
]

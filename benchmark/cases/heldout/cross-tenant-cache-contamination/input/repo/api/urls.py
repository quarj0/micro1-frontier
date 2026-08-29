from django.urls import path

from .views import TenantPreferenceView

urlpatterns = [
    path("preferences/", TenantPreferenceView.as_view(), name="tenant-preferences")
]

from django.urls import path

from .views import ChargeCreateView

urlpatterns = [path("charges/", ChargeCreateView.as_view(), name="charge-create")]

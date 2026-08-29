from django.urls import path

from .views import DocumentUploadView

urlpatterns = [path("uploads/", DocumentUploadView.as_view(), name="document-upload")]

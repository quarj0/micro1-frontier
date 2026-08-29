from django.urls import path

from .views import ProjectDetailView

urlpatterns = [
    path("projects/<int:project_id>/", ProjectDetailView.as_view(), name="project-detail")
]

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project
from .serializers import ProjectSerializer


def request_tenant_id(request):
    raw_tenant_id = request.headers.get("X-Tenant-ID")
    try:
        return int(raw_tenant_id)
    except (TypeError, ValueError) as exc:
        raise ValidationError({"tenant": "A numeric X-Tenant-ID header is required."}) from exc


class ProjectDetailView(APIView):
    def get(self, request, project_id):
        request_tenant_id(request)
        project = get_object_or_404(Project, pk=project_id)
        return Response(ProjectSerializer(project).data)

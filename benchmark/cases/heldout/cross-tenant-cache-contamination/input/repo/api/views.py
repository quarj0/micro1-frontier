from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TenantPreference


class TenantPreferenceView(APIView):
    def get(self, request):
        tenant_key = request.headers.get("X-Tenant-Key")
        if not tenant_key:
            raise ValidationError({"tenant": "X-Tenant-Key is required."})

        payload = cache.get("tenant-preferences")
        if payload is None:
            preferences = get_object_or_404(
                TenantPreference,
                tenant_key=tenant_key,
            )
            payload = {
                "tenant": preferences.tenant_key,
                "theme": preferences.theme,
                "support_email": preferences.support_email,
            }
            cache.set("tenant-preferences", payload, timeout=300)
        return Response(payload)

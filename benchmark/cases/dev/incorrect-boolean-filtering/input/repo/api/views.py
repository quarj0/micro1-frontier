from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView


INTEGRATIONS = [
    {"id": 1, "name": "Synthetic CRM", "active": True},
    {"id": 2, "name": "Synthetic Archive", "active": False},
    {"id": 3, "name": "Synthetic Alerts", "active": True},
]


class IntegrationListView(APIView):
    def get(self, request):
        integrations = INTEGRATIONS
        raw_active = request.query_params.get("active")
        if raw_active is not None:
            active = bool(raw_active)
            integrations = [item for item in integrations if item["active"] is active]
        return Response(integrations)


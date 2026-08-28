from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ProfileSerializer


class ProfileView(APIView):
    def get(self, request):
        profile = {
            "id": 7,
            "display_name": "Ada Lovelace",
            "email": "ada@example.test",
            "internal_note": "synthetic field that must not be exposed",
        }
        return Response(ProfileSerializer(profile).data)


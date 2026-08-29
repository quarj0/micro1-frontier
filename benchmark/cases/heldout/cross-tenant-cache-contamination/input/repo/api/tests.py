from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import TenantPreference


class TenantPreferenceSmokeTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_repeated_request_returns_preferences(self):
        TenantPreference.objects.create(
            tenant_key="synthetic",
            theme="dark",
            support_email="support@example.test",
        )

        first = self.client.get(
            "/api/preferences/",
            HTTP_X_TENANT_KEY="synthetic",
        )
        second = self.client.get(
            "/api/preferences/",
            HTTP_X_TENANT_KEY="synthetic",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.json(), first.json())

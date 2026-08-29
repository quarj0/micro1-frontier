from django.core.cache import cache
from rest_framework.test import APITestCase

from api.models import TenantPreference


class TenantCacheIsolationOracleTests(APITestCase):
    def setUp(self):
        cache.clear()
        TenantPreference.objects.create(
            tenant_key="alpha",
            theme="light",
            support_email="alpha@example.test",
        )
        TenantPreference.objects.create(
            tenant_key="beta",
            theme="dark",
            support_email="beta@example.test",
        )

    def get_preferences(self, tenant_key):
        return self.client.get(
            "/api/preferences/",
            HTTP_X_TENANT_KEY=tenant_key,
        )

    def assert_tenant_payload(self, tenant_key, expected_theme):
        response = self.get_preferences(tenant_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["tenant"], tenant_key)
        self.assertEqual(response.json()["theme"], expected_theme)
        self.assertEqual(
            response.json()["support_email"], f"{tenant_key}@example.test"
        )

    def test_cache_is_isolated_when_alpha_is_requested_first(self):
        self.assert_tenant_payload("alpha", "light")
        self.assert_tenant_payload("beta", "dark")
        self.assert_tenant_payload("alpha", "light")

    def test_cache_is_isolated_when_beta_is_requested_first(self):
        cache.clear()
        self.assert_tenant_payload("beta", "dark")
        self.assert_tenant_payload("alpha", "light")

    def test_warm_cache_does_not_make_unknown_tenant_valid(self):
        self.assert_tenant_payload("alpha", "light")
        response = self.get_preferences("missing")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("alpha@example.test", response.content.decode())

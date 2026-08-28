from rest_framework.test import APITestCase


class IntegrationSmokeTests(APITestCase):
    def test_unfiltered_endpoint_returns_all_integrations(self):
        response = self.client.get("/api/integrations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


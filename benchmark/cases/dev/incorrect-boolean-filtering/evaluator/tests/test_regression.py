from rest_framework.test import APITestCase


class BooleanFilterOracleTests(APITestCase):
    def ids_for(self, value):
        response = self.client.get("/api/integrations/", {"active": value})
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.json()]

    def test_false_selects_only_disabled_integrations(self):
        self.assertEqual(self.ids_for("false"), [2])
        self.assertEqual(self.ids_for("FALSE"), [2])

    def test_true_selects_only_active_integrations(self):
        self.assertEqual(self.ids_for("true"), [1, 3])
        self.assertEqual(self.ids_for("TRUE"), [1, 3])

    def test_unsupported_value_is_rejected(self):
        response = self.client.get("/api/integrations/", {"active": "sometimes"})
        self.assertEqual(response.status_code, 400)

    def test_omitted_filter_returns_all_integrations(self):
        response = self.client.get("/api/integrations/")
        self.assertEqual([item["id"] for item in response.json()], [1, 2, 3])


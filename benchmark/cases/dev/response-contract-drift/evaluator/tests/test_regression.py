from rest_framework.test import APITestCase


class ResponseContractOracleTests(APITestCase):
    def test_established_profile_contract_is_restored_exactly(self):
        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": 7,
                "display_name": "Ada Lovelace",
                "email": "ada@example.test",
            },
        )


from rest_framework.test import APITestCase


class ProfileSmokeTests(APITestCase):
    def test_profile_endpoint_is_available(self):
        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], 7)


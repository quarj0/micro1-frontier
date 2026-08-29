from rest_framework.test import APITestCase

from .models import Charge, Tenant


class ChargeIdempotencySmokeTests(APITestCase):
    def test_same_tenant_retry_returns_original_charge(self):
        tenant = Tenant.objects.create(name="Synthetic Account")
        headers = {
            "HTTP_X_TENANT_ID": str(tenant.pk),
            "HTTP_IDEMPOTENCY_KEY": "synthetic-retry-1",
        }

        first = self.client.post("/api/charges/", {"amount_cents": 1250}, format="json", **headers)
        replay = self.client.post("/api/charges/", {"amount_cents": 1250}, format="json", **headers)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["id"], first.json()["id"])
        self.assertTrue(replay.json()["replayed"])
        self.assertEqual(Charge.objects.count(), 1)

from rest_framework.test import APITestCase

from api.models import Charge, Tenant


class TenantIdempotencyIsolationOracleTests(APITestCase):
    def setUp(self):
        self.alpha = Tenant.objects.create(name="Synthetic Alpha")
        self.beta = Tenant.objects.create(name="Synthetic Beta")

    def create_charge(self, tenant, amount, key="shared-sdk-counter-0001"):
        return self.client.post(
            "/api/charges/",
            {"amount_cents": amount},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.pk),
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_same_key_is_independent_across_tenants(self):
        alpha_response = self.create_charge(self.alpha, 1200)
        beta_response = self.create_charge(self.beta, 3400)

        self.assertEqual(alpha_response.status_code, 201)
        self.assertEqual(beta_response.status_code, 201)
        self.assertNotEqual(alpha_response.json()["id"], beta_response.json()["id"])
        self.assertEqual(beta_response.json()["tenant_id"], self.beta.pk)
        self.assertEqual(beta_response.json()["amount_cents"], 3400)
        self.assertFalse(beta_response.json()["replayed"])
        self.assertEqual(Charge.objects.count(), 2)

    def test_each_tenant_still_deduplicates_its_own_retry(self):
        self.create_charge(self.alpha, 1200)
        self.create_charge(self.beta, 3400)

        alpha_replay = self.create_charge(self.alpha, 1200)
        beta_replay = self.create_charge(self.beta, 3400)

        self.assertEqual(alpha_replay.status_code, 200)
        self.assertEqual(beta_replay.status_code, 200)
        self.assertTrue(alpha_replay.json()["replayed"])
        self.assertTrue(beta_replay.json()["replayed"])
        self.assertEqual(Charge.objects.count(), 2)

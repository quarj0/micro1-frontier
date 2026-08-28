from rest_framework.test import APITestCase

from api.models import Order, OrderItem


class NestedWriteAtomicityOracleTests(APITestCase):
    def test_invalid_later_item_rolls_back_parent_and_earlier_item(self):
        response = self.client.post(
            "/api/orders/",
            {
                "reference": "SYNTHETIC-INVALID",
                "items": [
                    {"sku": "SYNTHETIC-GOOD", "quantity": 1},
                    {"sku": "SYNTHETIC-BAD", "quantity": 0},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_valid_nested_write_still_commits_everything(self):
        response = self.client.post(
            "/api/orders/",
            {
                "reference": "SYNTHETIC-VALID-HIDDEN",
                "items": [
                    {"sku": "SYNTHETIC-A", "quantity": 1},
                    {"sku": "SYNTHETIC-B", "quantity": 3},
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)


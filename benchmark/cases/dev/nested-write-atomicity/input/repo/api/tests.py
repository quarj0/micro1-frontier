from rest_framework.test import APITestCase

from .models import Order, OrderItem


class OrderSmokeTests(APITestCase):
    def test_valid_order_creates_all_rows(self):
        response = self.client.post(
            "/api/orders/",
            {
                "reference": "SYNTHETIC-VALID",
                "items": [{"sku": "SYNTHETIC-SKU", "quantity": 2}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)


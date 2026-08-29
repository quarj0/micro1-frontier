from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from api.models import Customer, Order, OrderItem


class OrderQueryBudgetOracleTests(APITestCase):
    def setUp(self):
        for index in range(12):
            customer = Customer.objects.create(name=f"Synthetic Customer {index}")
            order = Order.objects.create(
                customer=customer,
                reference=f"SYNTHETIC-{index:02d}",
            )
            OrderItem.objects.create(order=order, sku=f"SKU-{index}-A")
            OrderItem.objects.create(order=order, sku=f"SKU-{index}-B")

    def test_order_list_has_constant_query_budget_and_complete_payload(self):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(captured),
            3,
            "order list query count must not grow per customer or item collection",
        )
        self.assertEqual(len(response.json()), 12)
        self.assertEqual(
            response.json()[0],
            {
                "id": 1,
                "reference": "SYNTHETIC-00",
                "customer_name": "Synthetic Customer 0",
                "items": [
                    {"sku": "SKU-0-A"},
                    {"sku": "SKU-0-B"},
                ],
            },
        )

from rest_framework.test import APITestCase

from .models import Customer, Order, OrderItem


class OrderListSmokeTests(APITestCase):
    def test_order_list_returns_nested_contract(self):
        customer = Customer.objects.create(name="Synthetic Customer")
        order = Order.objects.create(customer=customer, reference="SYNTHETIC-ONE")
        OrderItem.objects.create(order=order, sku="SYNTHETIC-SKU")

        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["customer_name"], "Synthetic Customer")
        self.assertEqual(response.json()[0]["items"], [{"sku": "SYNTHETIC-SKU"}])

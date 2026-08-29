from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["sku"]


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name")
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "reference", "customer_name", "items"]

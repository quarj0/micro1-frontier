from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=40)
    quantity = serializers.IntegerField()


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemInputSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "reference", "items"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        items = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item in items:
            if item["quantity"] <= 0:
                raise serializers.ValidationError(
                    {"items": ["Quantity must be greater than zero."]}
                )
            OrderItem.objects.create(order=order, **item)
        return order


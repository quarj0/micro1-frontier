from rest_framework import generics

from .models import Order
from .serializers import OrderSerializer


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.order_by("id")
    serializer_class = OrderSerializer

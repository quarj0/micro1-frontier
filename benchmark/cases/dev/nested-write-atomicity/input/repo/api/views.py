from rest_framework import generics

from .models import Order
from .serializers import OrderCreateSerializer


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer


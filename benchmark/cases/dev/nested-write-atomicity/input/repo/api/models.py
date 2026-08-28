from django.db import models


class Order(models.Model):
    reference = models.CharField(max_length=40, unique=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    sku = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField()


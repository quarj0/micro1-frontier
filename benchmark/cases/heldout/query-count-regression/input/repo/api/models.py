from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=100)


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    reference = models.CharField(max_length=40, unique=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    sku = models.CharField(max_length=40)

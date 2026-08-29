from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=80)


class Charge(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    idempotency_key = models.CharField(max_length=120)
    amount_cents = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "idempotency_key"),
                name="unique_charge_key_per_tenant",
            )
        ]

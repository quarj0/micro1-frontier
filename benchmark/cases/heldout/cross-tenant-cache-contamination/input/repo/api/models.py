from django.db import models


class TenantPreference(models.Model):
    tenant_key = models.CharField(max_length=40, unique=True)
    theme = models.CharField(max_length=20)
    support_email = models.EmailField()

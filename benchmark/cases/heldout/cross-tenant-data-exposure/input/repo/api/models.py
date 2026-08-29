from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=80)


class Project(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    confidential_summary = models.CharField(max_length=200)

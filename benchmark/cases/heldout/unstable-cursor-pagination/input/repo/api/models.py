from django.db import models


class AuditEvent(models.Model):
    message = models.CharField(max_length=120)
    created_at = models.DateTimeField()

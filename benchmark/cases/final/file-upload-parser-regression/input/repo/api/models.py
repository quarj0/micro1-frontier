from django.db import models


class UploadedDocument(models.Model):
    filename = models.CharField(max_length=180)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()

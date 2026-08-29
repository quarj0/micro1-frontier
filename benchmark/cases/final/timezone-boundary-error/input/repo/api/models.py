from django.db import models


class CalendarEvent(models.Model):
    title = models.CharField(max_length=120)
    starts_at = models.DateTimeField()

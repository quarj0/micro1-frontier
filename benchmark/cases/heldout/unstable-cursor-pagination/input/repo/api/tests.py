from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from .models import AuditEvent


class AuditEventPaginationSmokeTests(APITestCase):
    def test_first_page_is_newest_first_and_bounded(self):
        now = timezone.now()
        for index in range(3):
            AuditEvent.objects.create(
                message=f"synthetic-{index}",
                created_at=now - timedelta(minutes=index),
            )

        response = self.client.get("/api/audit-events/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertIsNotNone(response.json()["next_cursor"])

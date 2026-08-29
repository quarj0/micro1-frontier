from datetime import UTC, datetime

from rest_framework.test import APITestCase

from .models import CalendarEvent


class CalendarDaySmokeTests(APITestCase):
    def test_utc_day_filters_with_half_open_bounds(self):
        included = CalendarEvent.objects.create(
            title="Synthetic UTC event",
            starts_at=datetime(2026, 2, 14, 12, 0, tzinfo=UTC),
        )
        CalendarEvent.objects.create(
            title="Synthetic next day",
            starts_at=datetime(2026, 2, 15, 0, 0, tzinfo=UTC),
        )

        response = self.client.get("/api/events/?date=2026-02-14&timezone=UTC")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [included.pk])

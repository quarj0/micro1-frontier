from datetime import UTC, datetime

from rest_framework.test import APITestCase

from api.models import CalendarEvent


class LocalCalendarBoundaryOracleTests(APITestCase):
    def create_event(self, title, year, month, day, hour, minute=0):
        return CalendarEvent.objects.create(
            title=title,
            starts_at=datetime(year, month, day, hour, minute, tzinfo=UTC),
        )

    def test_spring_dst_day_uses_new_york_local_boundaries(self):
        previous_local_day = self.create_event("previous local day", 2026, 3, 8, 4, 30)
        early = self.create_event("early local event", 2026, 3, 8, 5, 30)
        late = self.create_event("late local event", 2026, 3, 9, 3, 30)
        next_local_day = self.create_event("next local day", 2026, 3, 9, 4, 0)

        response = self.client.get(
            "/api/events/?date=2026-03-08&timezone=America/New_York"
        )

        self.assertEqual(response.status_code, 200)
        returned = [item["id"] for item in response.json()]
        self.assertEqual(returned, [early.pk, late.pk])
        self.assertNotIn(previous_local_day.pk, returned)
        self.assertNotIn(next_local_day.pk, returned)

    def test_positive_offset_day_does_not_use_utc_midnight(self):
        included = self.create_event("Tokyo morning", 2026, 6, 30, 15, 30)
        excluded = self.create_event("Tokyo next day", 2026, 7, 1, 15, 0)

        response = self.client.get("/api/events/?date=2026-07-01&timezone=Asia/Tokyo")

        self.assertEqual(response.status_code, 200)
        returned = [item["id"] for item in response.json()]
        self.assertEqual(returned, [included.pk])
        self.assertNotIn(excluded.pk, returned)

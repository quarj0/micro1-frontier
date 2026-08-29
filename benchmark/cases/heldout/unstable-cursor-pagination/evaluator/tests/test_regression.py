from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from api.models import AuditEvent


class StableCursorOracleTests(APITestCase):
    def setUp(self):
        newest = timezone.now().replace(microsecond=0)
        older = newest - timedelta(minutes=1)
        for message in ("new-a", "new-b", "new-c"):
            AuditEvent.objects.create(message=message, created_at=newest)
        for message in ("old-a", "old-b"):
            AuditEvent.objects.create(message=message, created_at=older)

    def traverse(self):
        ids = []
        cursor = None
        seen_cursors = set()
        while True:
            params = {"cursor": cursor} if cursor else {}
            response = self.client.get("/api/audit-events/", params)
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            ids.extend(item["id"] for item in payload["results"])
            cursor = payload["next_cursor"]
            if cursor is None:
                return ids
            self.assertNotIn(cursor, seen_cursors)
            seen_cursors.add(cursor)

    def test_traversal_returns_every_tied_record_once_in_stable_order(self):
        expected = list(
            AuditEvent.objects.order_by("-created_at", "-id").values_list(
                "id", flat=True
            )
        )

        first_traversal = self.traverse()
        second_traversal = self.traverse()

        self.assertEqual(first_traversal, expected)
        self.assertEqual(second_traversal, expected)
        self.assertEqual(len(first_traversal), len(set(first_traversal)))

    def test_invalid_cursor_is_rejected(self):
        response = self.client.get("/api/audit-events/", {"cursor": "not-a-cursor"})
        self.assertEqual(response.status_code, 400)

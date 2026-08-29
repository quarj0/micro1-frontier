import base64

from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditEvent


PAGE_SIZE = 2


def encode_cursor(event):
    value = event.created_at.isoformat().encode()
    return base64.urlsafe_b64encode(value).decode()


def decode_cursor(value):
    try:
        decoded = base64.b64decode(value.encode(), altchars=b"-_", validate=True).decode()
        timestamp = parse_datetime(decoded)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValidationError({"cursor": "Invalid cursor."}) from exc
    if timestamp is None:
        raise ValidationError({"cursor": "Invalid cursor."})
    return timestamp


class AuditEventListView(APIView):
    def get(self, request):
        events = AuditEvent.objects.order_by("-created_at", "-id")
        raw_cursor = request.query_params.get("cursor")
        if raw_cursor:
            events = events.filter(created_at__lt=decode_cursor(raw_cursor))

        page = list(events[: PAGE_SIZE + 1])
        has_more = len(page) > PAGE_SIZE
        page = page[:PAGE_SIZE]
        return Response(
            {
                "results": [
                    {
                        "id": event.pk,
                        "message": event.message,
                        "created_at": event.created_at.isoformat(),
                    }
                    for event in page
                ],
                "next_cursor": encode_cursor(page[-1]) if has_more else None,
            }
        )

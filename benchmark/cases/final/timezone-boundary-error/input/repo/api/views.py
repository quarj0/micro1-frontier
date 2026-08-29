from datetime import UTC, date, datetime, time, timedelta

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CalendarEvent
from .serializers import CalendarEventSerializer


class CalendarDayView(APIView):
    def get(self, request):
        try:
            requested_day = date.fromisoformat(request.query_params["date"])
        except (KeyError, ValueError) as exc:
            raise ValidationError({"date": "Use YYYY-MM-DD."}) from exc
        if not request.query_params.get("timezone"):
            raise ValidationError({"timezone": "An IANA timezone is required."})

        start = datetime.combine(requested_day, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        events = CalendarEvent.objects.filter(
            starts_at__gte=start,
            starts_at__lt=end,
        ).order_by("starts_at", "pk")
        return Response(CalendarEventSerializer(events, many=True).data)

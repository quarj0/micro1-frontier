from django.urls import path

from .views import CalendarDayView

urlpatterns = [path("events/", CalendarDayView.as_view(), name="calendar-day")]

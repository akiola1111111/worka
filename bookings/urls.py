from django.urls import path
from .views import (
    BookingCreateView, BookingStatusView, ClientConfirmCompletionView,
    WorkerBookingListView, WorkerMarkCompleteView,
)

urlpatterns = [
    path("", BookingCreateView.as_view(), name="booking-create"),
    path("track/<uuid:tracking_code>/", BookingStatusView.as_view(), name="booking-status"),
    path("track/<uuid:tracking_code>/confirm-completion/", ClientConfirmCompletionView.as_view(), name="booking-confirm"),
    path("mine/", WorkerBookingListView.as_view(), name="worker-bookings"),
    path("<int:pk>/mark-complete/", WorkerMarkCompleteView.as_view(), name="booking-mark-complete"),
]

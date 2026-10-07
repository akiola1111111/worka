from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Booking
from .serializers import BookingCreateSerializer, BookingStatusSerializer, WorkerBookingSerializer


class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.AllowAny]


class BookingStatusView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingStatusSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "tracking_code"
    lookup_url_kwarg = "tracking_code"


class ClientConfirmCompletionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, tracking_code):
        booking = get_object_or_404(Booking, tracking_code=tracking_code)
        if booking.status != "completed":
            return Response(
                {"detail": f"Booking must be 'completed' by the worker first (currently '{booking.status}')."},
                status=400,
            )
        booking.status = "paid_out"
        booking.save(update_fields=["status"])
        return Response(BookingStatusSerializer(booking).data)


class WorkerBookingListView(generics.ListAPIView):
    serializer_class = WorkerBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(worker=self.request.user)


class WorkerMarkCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, worker=request.user)
        if booking.status != "in_progress":
            return Response(
                {"detail": f"Booking must be 'in_progress' (currently '{booking.status}')."}, status=400
            )
        booking.status = "completed"
        booking.completed_at = timezone.now()
        booking.save(update_fields=["status", "completed_at"])
        return Response(WorkerBookingSerializer(booking).data)

from rest_framework import serializers
from .models import Booking
from accounts.serializers import WorkerPublicSerializer
from services.serializers import ServiceCategorySerializer


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "client_name", "client_phone", "client_location_text",
            "client_latitude", "client_longitude", "worker", "category",
            "description", "preferred_date", "tracking_code",
        ]
        read_only_fields = ["id", "tracking_code"]


class BookingStatusSerializer(serializers.ModelSerializer):
    worker = WorkerPublicSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "tracking_code", "worker", "category", "description", "status",
            "status_display", "quoted_amount", "preferred_date", "created_at",
        ]


class WorkerBookingSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "client_name", "client_location_text", "category", "description",
            "preferred_date", "status", "status_display", "quoted_amount", "created_at",
        ]

from rest_framework import serializers
from .models import Worker
from services.serializers import ServiceCategorySerializer
from .utils import haversine_km


class WorkerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = [
            "phone_number", "full_name", "category", "bio", "years_of_experience",
            "region", "town", "latitude", "longitude", "momo_number", "momo_network",
        ]

    def create(self, validated_data):
        return Worker.objects.create_user(**validated_data)


class WorkerProfileSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)

    class Meta:
        model = Worker
        fields = [
            "id", "phone_number", "full_name", "category", "bio", "years_of_experience",
            "region", "town", "latitude", "longitude", "profile_photo",
            "id_document_front", "id_document_back", "id_type",
            "is_verified", "is_available", "rating_avg", "rating_count",
            "momo_number", "momo_network", "date_joined",
        ]
        read_only_fields = ["id", "phone_number", "is_verified", "rating_avg", "rating_count", "date_joined"]


class WorkerPublicSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = [
            "id", "full_name", "category", "bio", "years_of_experience",
            "region", "town", "profile_photo", "is_verified", "is_available",
            "rating_avg", "rating_count", "distance_km",
        ]

    def get_distance_km(self, obj):
        client_lat = self.context.get("client_lat")
        client_lng = self.context.get("client_lng")
        if client_lat is None or client_lng is None:
            return None
        return haversine_km(client_lat, client_lng, obj.latitude, obj.longitude)

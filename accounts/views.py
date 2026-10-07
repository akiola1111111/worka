from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .models import Worker
from .serializers import WorkerRegisterSerializer, WorkerProfileSerializer, WorkerPublicSerializer


def _tokens_for(worker):
    refresh = RefreshToken.for_user(worker)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "worker": WorkerProfileSerializer(worker).data,
    }


class RegisterWorkerView(generics.CreateAPIView):
    """
    Registers a worker and logs them straight in — no phone verification step.
    (Worth adding some other safeguard, like a PIN, before a public launch —
    right now anyone who knows a phone number could register or log in as it.)
    """

    queryset = Worker.objects.all()
    serializer_class = WorkerRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        worker = serializer.save()
        return Response(_tokens_for(worker), status=201)


class LoginView(APIView):
    """Log in with just a phone number — no code sent. See RegisterWorkerView's note."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone_number", "").strip()
        if not phone:
            return Response({"detail": "phone_number is required"}, status=400)
        worker = Worker.objects.filter(phone_number=phone).first()
        if not worker:
            return Response({"detail": "No worker registered with this number"}, status=404)
        return Response(_tokens_for(worker))


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ToggleAvailabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        worker = request.user
        worker.is_available = not worker.is_available
        worker.save(update_fields=["is_available"])
        return Response({"is_available": worker.is_available})


class WorkerSearchView(generics.ListAPIView):
    serializer_class = WorkerPublicSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name", "town"]

    def get_queryset(self):
        qs = Worker.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        region = self.request.query_params.get("region")
        available_only = self.request.query_params.get("available_only")
        if category:
            qs = qs.filter(category_id=category)
        if region:
            qs = qs.filter(region=region)
        if available_only == "true":
            qs = qs.filter(is_available=True)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        try:
            ctx["client_lat"] = float(self.request.query_params.get("lat"))
            ctx["client_lng"] = float(self.request.query_params.get("lng"))
        except (TypeError, ValueError):
            ctx["client_lat"] = ctx["client_lng"] = None
        return ctx

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if self.get_serializer_context()["client_lat"] is not None:
            results_key = "results" if "results" in response.data else None
            items = response.data[results_key] if results_key else response.data
            items = sorted(items, key=lambda w: (w["distance_km"] is None, w["distance_km"]))
            if results_key:
                response.data[results_key] = items
            else:
                response.data = items
        return response


class WorkerPublicDetailView(generics.RetrieveAPIView):
    queryset = Worker.objects.filter(is_active=True)
    serializer_class = WorkerPublicSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        try:
            ctx["client_lat"] = float(self.request.query_params.get("lat"))
            ctx["client_lng"] = float(self.request.query_params.get("lng"))
        except (TypeError, ValueError):
            ctx["client_lat"] = ctx["client_lng"] = None
        return ctx

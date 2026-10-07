from rest_framework import generics, permissions
from .models import ServiceCategory
from .serializers import ServiceCategorySerializer


class ServiceCategoryListView(generics.ListAPIView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.AllowAny]

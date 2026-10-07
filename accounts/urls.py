from django.urls import path
from .views import (
    RegisterWorkerView, LoginView, MyProfileView,
    ToggleAvailabilityView, WorkerSearchView, WorkerPublicDetailView,
)

urlpatterns = [
    path("register/", RegisterWorkerView.as_view(), name="worker-register"),
    path("login/", LoginView.as_view(), name="worker-login"),
    path("me/", MyProfileView.as_view(), name="my-profile"),
    path("me/toggle-availability/", ToggleAvailabilityView.as_view(), name="toggle-availability"),
    path("workers/", WorkerSearchView.as_view(), name="worker-search"),
    path("workers/<int:pk>/", WorkerPublicDetailView.as_view(), name="worker-detail"),
]

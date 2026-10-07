from django.urls import path
from .views import InitializePaymentView, VerifyPaymentView, PaystackWebhookView, ReleaseEscrowView

urlpatterns = [
    path("booking/<uuid:tracking_code>/initialize/", InitializePaymentView.as_view(), name="payment-init"),
    path("verify/<str:reference>/", VerifyPaymentView.as_view(), name="payment-verify"),
    path("webhook/", PaystackWebhookView.as_view(), name="payment-webhook"),
    path("booking/<uuid:tracking_code>/release/", ReleaseEscrowView.as_view(), name="payment-release"),
]

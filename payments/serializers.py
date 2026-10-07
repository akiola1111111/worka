from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "booking", "amount", "commission_amount", "payout_amount",
            "paystack_reference", "paystack_authorization_url", "status",
            "paid_at", "released_at",
        ]
        read_only_fields = fields
